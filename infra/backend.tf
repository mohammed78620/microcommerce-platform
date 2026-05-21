terraform {
  backend "s3" {
    bucket         = "microcommerce-tfstate-prod-uk01"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    use_lockfile   = true
  }
}