# =============================================================================
# API Gateway — single public entry point in front of the microservice EC2
# instances, path-routed to match the old nginx /api/<service>/ routing,
# with request throttling (rate limiting) applied at the stage level.
#
# Uses HTTP API (v2), not REST API (v1): v1's {proxy+} HTTP_PROXY integration
# strips a trailing "/" from the forwarded path, which breaks any Django view
# whose URL pattern requires one (APPEND_SLASH issues a 301 that drops POST
# bodies). HTTP API v2 forwards the raw incoming path byte-for-byte.
# =============================================================================

resource "aws_apigatewayv2_api" "main" {
  name          = "microcommerce-api-gateway"
  description   = "Routes /api/<service>/* to the microservice EC2 instances"
  protocol_type = "HTTP"
}

# ---- root of each service, e.g. ANY /api/auth ----

resource "aws_apigatewayv2_integration" "service_root" {
  for_each = local.microservices

  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "HTTP_PROXY"
  integration_method = "ANY"
  integration_uri    = "http://${aws_eip.microservice[each.key].public_ip}:${each.value.port}/"
}

resource "aws_apigatewayv2_route" "service_root" {
  for_each = local.microservices

  api_id    = aws_apigatewayv2_api.main.id
  route_key = "ANY /api/${each.value.path}"
  target    = "integrations/${aws_apigatewayv2_integration.service_root[each.key].id}"
}

# ---- everything under each service, e.g. ANY /api/auth/{proxy+} ----

resource "aws_apigatewayv2_integration" "service_proxy" {
  for_each = local.microservices

  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "HTTP_PROXY"
  integration_method = "ANY"
  integration_uri    = "http://${aws_eip.microservice[each.key].public_ip}:${each.value.port}/{proxy}"
}

resource "aws_apigatewayv2_route" "service_proxy" {
  for_each = local.microservices

  api_id    = aws_apigatewayv2_api.main.id
  route_key = "ANY /api/${each.value.path}/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.service_proxy[each.key].id}"
}

# ---- stage + rate limiter (applies to every route by default) ----

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_rate_limit  = var.api_gateway_rate_limit
    throttling_burst_limit = var.api_gateway_burst_limit
  }
}

output "api_gateway_url" {
  description = "Base invoke URL for the API Gateway (CloudFront proxies /api/* here)."
  value       = aws_apigatewayv2_api.main.api_endpoint
}
