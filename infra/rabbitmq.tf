resource "aws_security_group" "rabbitmq" {
  name        = "microcommerce-rabbitmq-sg"
  description = "Allow RabbitMQ access from app instance"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "AMQP"
    from_port       = 5672
    to_port         = 5672
    protocol        = "tcp"
    security_groups = [aws_security_group.host.id]
  }

  ingress {
    description     = "RabbitMQ Management UI"
    from_port       = 15672
    to_port         = 15672
    protocol        = "tcp"
    security_groups = [aws_security_group.host.id]
  }

  ingress {
    description = "Allow SSH"
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
    Name = "microcommerce-rabbitmq-sg"
  }
}

resource "aws_instance" "rabbitmq" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = "t3.micro"
  subnet_id                   = data.aws_subnets.default.ids[0]
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.rabbitmq.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2.name
  key_name                    = local.use_key_pair ? aws_key_pair.deploy[0].key_name : null

  user_data = <<-EOF
    #!/bin/bash
    set -e
    yum update -y
    amazon-linux-extras install -y docker
    systemctl enable --now docker
    usermod -aG docker ec2-user
    docker run -d \
      --name rabbitmq \
      --restart always \
      -p 5672:5672 \
      -p 15672:15672 \
      -e RABBITMQ_DEFAULT_USER=${var.rabbitmq_user} \
      -e RABBITMQ_DEFAULT_PASS=${var.rabbitmq_password} \
      rabbitmq:management
  EOF

  tags = {
    Name = "microcommerce-rabbitmq"
  }
}