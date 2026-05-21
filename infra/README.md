# AWS Terraform Deployment

This directory contains minimal Terraform configuration to deploy the repository to AWS using a single EC2 host.

## What it deploys

- AWS EC2 instance in `us-east-1`
- Security group for HTTP, Docker service ports, and SSH
- IAM role for AWS Systems Manager (SSM)
- Optional SSH key pair if `public_key_path` is provided

## Usage

1. Install Terraform.
2. Set required variables:
   - `repository_url` — Git URL for this repository.
   - `public_key_path` — optional path to an SSH public key file.
3. Initialize and apply:

```bash
cd infra
terraform init
terraform apply
```

## Notes

- The EC2 instance uses Docker Compose to start containers from `docker-compose.yaml`.
- If the repository URL is not set, Terraform will still create infrastructure, but the application will not be cloned or started automatically.
- You can connect with SSM Session Manager even when no SSH key is provided.
