output "evidence_bucket_name" {
  value = aws_s3_bucket.evidence.id
}

output "evidence_bucket_arn" {
  value = aws_s3_bucket.evidence.arn
}

output "seeded_unencrypted_bucket_name" {
  value = var.create_seeded_unencrypted_bucket ? aws_s3_bucket.seeded_unencrypted[0].id : null
}
