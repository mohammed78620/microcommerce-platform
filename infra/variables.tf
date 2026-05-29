variable "aws_region" {
  description = "AWS region for deployment."
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type used for the application host."
  type        = string
  default     = "t3.micro"
}

variable "repository_url" {
  description = "Git repository URL for the application source code."
  type        = string
  default     = ""
}

variable "repository_branch" {
  description = "Git branch to deploy from the repository."
  type        = string
  default     = "main"
}

variable "public_key_path" {
  description = "Optional path to an SSH public key file for EC2 access. If empty, access is available via SSM only."
  type        = string
  default     = ""
}

variable "frontend_bucket_name" {
  description = "Optional explicit name for the frontend S3 bucket. If empty Terraform will generate one." 
  type        = string
  default     = ""
}

variable "rabbitmq_user" {
  description = "RabbitMQ username"
  type        = string
  default     = "admin"
}

variable "rabbitmq_password" {
  description = "RabbitMQ password"
  type        = string
  sensitive   = true
}

variable "django_secret_key" {
  description = "Django secret key"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "RDS password"
  type        = string
  sensitive   = true
}