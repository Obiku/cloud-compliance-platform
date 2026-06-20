# Evidence bucket: secure baseline used from Phase 5 onward to store audit evidence.
resource "aws_s3_bucket" "evidence" {
  bucket = "${var.name_prefix}-evidence-${var.account_id}"

  tags = merge(var.tags, {
    Name    = "${var.name_prefix}-evidence"
    Purpose = "evidence-store"
  })
}

resource "aws_s3_bucket_versioning" "evidence" {
  bucket = aws_s3_bucket.evidence.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "evidence" {
  bucket = aws_s3_bucket.evidence.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "evidence" {
  bucket                  = aws_s3_bucket.evidence.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- Phase 1 seeded issue ---
# Intentionally insecure bucket: no server-side encryption configured. Public access is
# still blocked (no need to risk real public exposure to demonstrate an encryption gap).
# Detected in Phase 3 (Security Hub / Config), remediated in Phase 4/5. Do not replicate
# this pattern elsewhere in the project.
resource "aws_s3_bucket" "seeded_unencrypted" {
  count  = var.create_seeded_unencrypted_bucket ? 1 : 0
  bucket = "${var.name_prefix}-legacy-data-${var.account_id}"

  tags = merge(var.tags, {
    Name    = "${var.name_prefix}-legacy-data"
    Purpose = "phase1-seeded-issue"
  })
}

resource "aws_s3_bucket_public_access_block" "seeded_unencrypted" {
  count                   = var.create_seeded_unencrypted_bucket ? 1 : 0
  bucket                  = aws_s3_bucket.seeded_unencrypted[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
