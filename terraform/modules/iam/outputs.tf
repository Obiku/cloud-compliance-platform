output "compliance_auditors_group_name" {
  value = aws_iam_group.compliance_auditors.name
}

output "cloud_engineers_group_name" {
  value = aws_iam_group.cloud_engineers.name
}

output "compliance_admins_group_name" {
  value = aws_iam_group.compliance_admins.name
}

output "seeded_legacy_admin_user_name" {
  value = var.create_seeded_admin_user ? aws_iam_user.seeded_legacy_admin[0].name : null
}
