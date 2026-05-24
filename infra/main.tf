data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["137112412989"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

locals {
  use_key_pair = trimspace(var.public_key_path) != ""
}

resource "aws_key_pair" "deploy" {
  count      = local.use_key_pair ? 1 : 0
  key_name   = "microcommerce-deploy-key"
  public_key = file(var.public_key_path)
}

resource "aws_security_group" "host" {
  name        = "microcommerce-host-sg"
  description = "Allow web access and SSH/SSM to the deployment host."
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Allow HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow web ports for Django services"
    from_port   = 8000
    to_port     = 9000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow SSH when a key is supplied"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "microcommerce-host-sg"
  }
}

resource "aws_iam_role" "ec2_ssm" {
  name               = "microcommerce-ec2-ssm-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role_policy.json
}

data "aws_iam_policy_document" "ec2_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ec2_ssm.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2" {
  name = "microcommerce-ec2-instance-profile"
  role = aws_iam_role.ec2_ssm.name
}

resource "aws_eip" "app" {
  domain = "vpc"

  tags = {
    Name = "microcommerce-app-eip"
  }
}

resource "aws_eip_association" "app" {
  instance_id   = aws_instance.app.id
  allocation_id = aws_eip.app.id
}

output "app_public_dns" {
  value = aws_instance.app.public_dns
}

resource "aws_instance" "app" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnets.default.ids[0]
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.host.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2.name
  key_name                    = local.use_key_pair ? aws_key_pair.deploy[0].key_name : null

  depends_on = [aws_instance.rabbitmq, aws_elasticache_cluster.redis]

  user_data = <<-EOF
                #!/bin/bash
                set -e
                yum update -y
                amazon-linux-extras install -y docker
                yum install -y git
                systemctl enable --now docker
                usermod -aG docker ec2-user
                mkdir -p /usr/local/lib/docker/cli-plugins
                curl -L "https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-linux-x86_64" -o /usr/local/lib/docker/cli-plugins/docker-compose
                chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

                if [ -z "$${REPOSITORY_URL}" ]; then
                  REPOSITORY_URL="${var.repository_url}"
                fi

                if [ -n "$${REPOSITORY_URL}" ]; then
                  cd /home/ec2-user
                  if [ ! -d app ]; then
                    git clone -b "${var.repository_branch}" "$${REPOSITORY_URL}" app
                  else
                    cd app
                    git pull origin "${var.repository_branch}"
                  fi

                  # ---- BREAKS THE CYCLE HERE ----
                  # We use a wildcard fallback string so Django allows requests from CloudFront.
                  # This bypasses the need to wait for CloudFront to generate an ID first!
                  cat > /home/ec2-user/app/.env <<ENVFILE
RABBITMQ_HOST=${aws_instance.rabbitmq.private_ip}
RABBITMQ_USER=${var.rabbitmq_user}
RABBITMQ_PASSWORD=${var.rabbitmq_password}
ALLOWED_HOSTS=localhost,127.0.0.1,auth-service,orders,products,emails,*.cloudfront.net
SECRET_KEY=${var.django_secret_key}
REDIS_URL=redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0
ENVFILE

                  cd /home/ec2-user/app
                  /usr/local/lib/docker/cli-plugins/docker-compose -f docker-compose.yaml up -d
                else
                  echo "WARNING: repository_url is empty. Set repository_url variable to deploy the application." >/var/log/deploy-warning.log
                fi
                EOF

  tags = {
    Name = "microcommerce-app-host"
  }
}