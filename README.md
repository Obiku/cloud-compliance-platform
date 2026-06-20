# Cloud Compliance Automation Platform

End-to-end AWS compliance automation platform, governed through ServiceNow IRM: Terraform infrastructure baseline, policy-as-code CI/CD, continuous AWS monitoring, Python/boto3 governance automation, a formal control testing program, and GRC reporting.

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the full phase-by-phase plan and [DEVLOG.md](DEVLOG.md) for a running log of what's been built so far.

## Frameworks

ISO 27001:2022 · SOC 2 Type II · NIST Cybersecurity Framework · CIS AWS Benchmarks

## Project structure

```
├── terraform/        # AWS infrastructure as code (VPC, IAM, S3, compute)
├── python/           # boto3 automation: IAM governance, evidence collection, ServiceNow integration
├── .github/workflows/ # CI/CD: terraform plan, Checkov/tfsec, Bandit, pip-audit
├── docs/             # Phase documentation, control matrix, RCM
└── workpapers/        # Control testing workpapers and evidence references
```

## Status

See [DEVLOG.md](DEVLOG.md).
