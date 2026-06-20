# This module deliberately does NOT create an AWS Config recorder, delivery channel,
# Security Hub subscription, or GuardDuty detector. This AWS account already runs all
# four for an unrelated project ("access-review-prod") - those are account/region-wide
# singletons, so creating a second one would either fail or hijack the existing setup.
# See docs/phase3_monitoring.md for what's already in place and what this module adds
# on top of it.

resource "aws_config_conformance_pack" "nist_csf" {
  name          = "${var.name_prefix}-nist-csf"
  template_body = file("${path.module}/templates/nist-csf.yaml")
}
