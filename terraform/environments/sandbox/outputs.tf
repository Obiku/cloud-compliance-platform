output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnet_ids" {
  value = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.vpc.private_subnet_ids
}

output "evidence_bucket_name" {
  value = module.s3.evidence_bucket_name
}

output "seeded_unencrypted_bucket_name" {
  value = module.s3.seeded_unencrypted_bucket_name
}

output "seeded_legacy_admin_user_name" {
  value = module.iam.seeded_legacy_admin_user_name
}

output "automation_lambda_arn" {
  value = module.compute.automation_lambda_arn
}
