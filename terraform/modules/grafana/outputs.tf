output "workspace_endpoint" {
  description = "Grafana workspace URL - null when create_workspace is false"
  value       = var.create_workspace ? aws_grafana_workspace.this[0].endpoint : null
}

output "workspace_id" {
  description = "Grafana workspace ID - null when create_workspace is false"
  value       = var.create_workspace ? aws_grafana_workspace.this[0].id : null
}

output "grafana_admin_username" {
  value = aws_identitystore_user.grafana_admin.user_name
}

output "dashboard_importer_token" {
  description = "Service account token for the Grafana HTTP API - null when create_workspace is false"
  value       = var.create_workspace ? aws_grafana_workspace_service_account_token.dashboard_importer[0].key : null
  sensitive   = true
}
