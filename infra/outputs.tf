output "ec2_public_ip" {
  description = "Public IP address of the EC2 host."
  value       = aws_instance.app.public_ip
}

output "app_url" {
  description = "HTTP URL for the deployed application host."
  value       = "http://${aws_instance.app.public_ip}"
}

output "rabbitmq_private_ip" {
  value = aws_instance.rabbitmq.private_ip
}

output "rabbitmq_public_ip" {
  value = aws_instance.rabbitmq.public_ip
}

output "frontend_bucket" {
  description = "S3 bucket for frontend assets"
  value       = aws_s3_bucket.frontend.bucket
}

output "cloudfront_domain" {
  description = "CloudFront domain name for the frontend"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_id" {
  description = "CloudFront distribution id"
  value       = aws_cloudfront_distribution.frontend.id
}

output "app_public_ip" {
  description = "Elastic IP of the app EC2 instance"
  value       = aws_eip.app.public_ip
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}