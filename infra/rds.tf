# =============================================================================
# DB subnet group
# Uses the looked-up default subnets — they already span multiple AZs.
# =============================================================================

resource "aws_db_subnet_group" "main" {
  name        = "main-db-subnet-group"
  description = "Default VPC subnets for all Django service databases"
  subnet_ids  = data.aws_subnets.default.ids

  tags = { Name = "main-db-subnet-group" }
}

# =============================================================================
# Parameter group
# =============================================================================

resource "aws_db_parameter_group" "postgres15" {
  name        = "django-postgres15"
  family      = "postgres15"
  description = "Postgres 15 settings for Django microservices"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"   # log queries taking longer than 1 s
  }

  tags = { Name = "django-postgres15-params" }
}

# =============================================================================
# RDS security group
# Only accepts Postgres connections from the EC2 host security group.
# =============================================================================

resource "aws_security_group" "rds" {
  name        = "sg_rds"
  description = "RDS: Postgres ingress from EC2 host only"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "Postgres from EC2 host security group"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.host.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "sg_rds" }
}

locals {
  databases = {
    auth-service = "auth_service"
    orders       = "orders"
    products     = "products"
    emails       = "emails"
  }
}

# =============================================================================
# RDS instances — one per microservice
# =============================================================================

resource "aws_db_instance" "service_db" {
  for_each = local.databases

  identifier        = "${each.key}-postgres"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = each.value
  username = "admin_${each.value}"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  multi_az            = true
  publicly_accessible = false

  backup_retention_period           = 0 # aws free tier
  backup_window                     = "03:00-04:00"
  maintenance_window                = "Mon:04:00-Mon:05:00"

  deletion_protection               = false # should probably be true in production environment
  skip_final_snapshot               = false
  final_snapshot_identifier         = "${each.key}-postgres-final-snapshot"

  tags = { Service = each.key }
}
