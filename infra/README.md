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
terraform init -reconfigure
terraform apply
```
4. update .env URL's  in react app with cloudfront_domain
```bash
terraform output --raw cloudfront_domain
```
5. build react app and publish to s3
```bash
cd ..\frontend
aws s3 sync build/ s3://"$(terraform -chdir="../infra" output --raw frontend_bucket)" --delete
```
6. Invalidate cache
```bash
aws cloudfront create-invalidation --distribution-id $(terraform -chdir="../infra" output --raw cloudfront_id) --paths "/*"
```
## Notes

- The EC2 instance uses Docker Compose to start containers from `docker-compose.yaml`.
- If the repository URL is not set, Terraform will still create infrastructure, but the application will not be cloned or started automatically.
- You can connect with SSM Session Manager even when no SSH key is provided.
- to access backend machine run
```bash
aws ssm start-session --target $(aws ec2 describe-instances --filters "Name=tag:Name,Values=microcommerce-app-host" --query "Reservations[0].Instances[0].InstanceId" --output text) --document-name AWS-StartInteractiveCommand --parameters command="sudo su -"
```
