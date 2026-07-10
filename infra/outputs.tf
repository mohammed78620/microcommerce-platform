output "microservice_public_ips" {
  description = "Public (Elastic) IP per microservice EC2 instance."
  value = {
    for k, eip in aws_eip.microservice : k => eip.public_ip
  }
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

output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "db_endpoints" {
  value = {
    for k, db in aws_db_instance.service_db :
    k => db.endpoint
  }
}