# =============================================================================
# One EC2 instance per microservice.
# Each instance clones the repo and runs only its own docker-compose file.
# =============================================================================

locals {
  microservices = {
    auth-service = { port = 8004, compose_file = "docker-compose.auth.yaml", path = "auth" }
    products     = { port = 8002, compose_file = "docker-compose.products.yaml", path = "products" }
    orders       = { port = 8003, compose_file = "docker-compose.orders.yaml", path = "orders" }
    emails       = { port = 8001, compose_file = "docker-compose.emails.yaml", path = "emails" }
  }
}

resource "aws_eip" "microservice" {
  for_each = local.microservices
  domain   = "vpc"

  tags = {
    Name = "microcommerce-${each.key}-eip"
  }
}

resource "aws_eip_association" "microservice" {
  for_each      = local.microservices
  instance_id   = aws_instance.microservice[each.key].id
  allocation_id = aws_eip.microservice[each.key].id
}

resource "aws_instance" "microservice" {
  for_each = local.microservices

  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnets.default.ids[0]
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.host.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2.name
  key_name                    = local.use_key_pair ? aws_key_pair.deploy[0].key_name : null
  user_data_replace_on_change = true

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

                  cat > /home/ec2-user/app/.env <<ENVFILE
RABBITMQ_HOST=${aws_instance.rabbitmq.private_ip}
RABBITMQ_USER=${var.rabbitmq_user}
RABBITMQ_PASSWORD=${var.rabbitmq_password}
ALLOWED_HOSTS=localhost,127.0.0.1,auth-service,orders,products,emails,*.cloudfront.net,.execute-api.${var.aws_region}.amazonaws.com,${aws_eip.microservice[each.key].public_ip}
SECRET_KEY=${var.django_secret_key}
AUTH_SERVICE_URL=${aws_apigatewayv2_api.main.api_endpoint}/api/auth/
PRODUCTS_SERVICE_URL=${aws_apigatewayv2_api.main.api_endpoint}/api/products/
REDIS_URL=redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0
AUTH_SERVICE_HOST=${aws_db_instance.service_db["auth-service"].address}
AUTH_SERVICE_DATABASE_NAME=${aws_db_instance.service_db["auth-service"].db_name}
AUTH_SERVICE_DATABASE_USER=${aws_db_instance.service_db["auth-service"].username}
PRODUCTS_HOST=${aws_db_instance.service_db["products"].address}
PRODUCTS_DATABASE_NAME=${aws_db_instance.service_db["products"].db_name}
PRODUCTS_DATABASE_USER=${aws_db_instance.service_db["products"].username}
ORDERS_HOST=${aws_db_instance.service_db["orders"].address}
ORDERS_DATABASE_NAME=${aws_db_instance.service_db["orders"].db_name}
ORDERS_DATABASE_USER=${aws_db_instance.service_db["orders"].username}
EMAILS_HOST=${aws_db_instance.service_db["emails"].address}
EMAILS_DATABASE_NAME=${aws_db_instance.service_db["emails"].db_name}
EMAILS_DATABASE_USER=${aws_db_instance.service_db["emails"].username}
DATABASE_PASSWORD=${var.db_password}

ENVFILE

                  cd /home/ec2-user/app
                  /usr/local/lib/docker/cli-plugins/docker-compose -f ${each.value.compose_file} up -d
                else
                  echo "WARNING: repository_url is empty. Set repository_url variable to deploy the application." >/var/log/deploy-warning.log
                fi
                EOF

  tags = {
    Name    = "microcommerce-${each.key}-host"
    Service = each.key
  }
}
