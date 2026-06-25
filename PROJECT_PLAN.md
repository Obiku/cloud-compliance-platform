# Cloud Compliance Automation Platform: Project Plan

A single end to end AWS compliance automation project, governed through ServiceNow IRM, built to provide real, demonstrable, hands on GRC engineering experience.

The platform runs in five layers: a Terraform based infrastructure baseline with policy as code CI/CD, a continuously monitored AWS environment, a Python automation and evidence layer, a ServiceNow IRM governance layer with role based access control, and a formal control testing program tying it all together, reported through a metrics dashboard.

All code is written in Python.

---

## Phase 0: Foundations

Set up the environment everything else will run in.

- Create an AWS sandbox account with billing alarms and budgets configured
- Create a GitHub repository
- Create a ServiceNow Personal Developer Instance and activate the IRM plugin
- Configure Terraform remote state with an S3 backend and DynamoDB locking

---

## Phase 1: Compliant infrastructure baseline (Terraform)

Build the core AWS environment as code, with a couple of realistic, intentional issues seeded in for later phases to detect and remediate.

- Write Terraform modules for VPC, IAM (users, groups, and roles designed around RBAC), S3, and EC2/Lambda compute
- Seed an IAM user with AdministratorAccess and no MFA
- Seed an S3 bucket without encryption at rest
- Document the before state for later reference

---

## Phase 2: Policy as code CI/CD pipeline

Enforce governance at the pipeline level, before infrastructure is ever deployed.

- Build a GitHub Actions workflow combining a Terraform plan, a static IaC scan mapped to the CIS AWS Benchmark, a Python SAST scan, and a dependency vulnerability scan
- Configure the pipeline to block merges on critical and high findings from any stage
- Document which policy as code rules map to which framework controls
- Track any accepted findings, including false positives and accepted risk, in a vulnerability log with an owner and justification for each, so the process produces a real audit trail rather than just scanner output

---

## Phase 3: Continuous cloud compliance monitoring

Turn on AWS native continuous monitoring and confirm it correctly detects the Phase 1 issues.

- Enable AWS Config with a conformance pack mapped to the NIST Cybersecurity Framework
- Enable Security Hub with the CIS AWS Foundations and AWS Foundational Security Best Practices standards
- Enable GuardDuty
- Enable an account level CloudTrail
- Confirm the seeded IAM and S3 issues are flagged correctly

---

## Phase 4: IAM governance automation (Python and boto3)

Automate detection and remediation of excessive privileges and dormant accounts.

- Write a scheduled scan that checks IAM for users without MFA, access keys older than 90 days, roles unused for 90 or more days, and policies granting AdministratorAccess
- Generate a remediation report from the scan
- Add an approval gated remediation step for the highest risk findings
- Run it against the Phase 1 environment and capture before and after evidence

---

## Phase 5: Automated evidence collection pipeline

Automate the collection and organisation of audit evidence.

- Write scripts to pull Config compliance snapshots, Security Hub findings, and CloudTrail samples
- Store outputs as timestamped artifacts in S3, organised by control ID
- Build an initial control matrix mapping each evidence artifact to ISO 27001 Annex A clauses and SOC 2 Trust Services Criteria

---

## Phase 6: Control testing program

Apply a formal, industry standard control testing methodology to the controls built so far.

- Expand the control matrix into a full Risk and Control Matrix: control ID, description, framework mappings, owner, control type, nature, and frequency
- For controls where a script has full access to the population, test the entire population
- For manual or periodic controls, define a population and select an appropriate sample
- For automated controls, test by re-performance: reintroduce a seeded issue and time how long the control takes to detect it
- For manual controls, test by inspection: check sampled evidence artifacts against criteria
- Document results in a workpaper covering control ID, test date, procedure, sample or population, result, evidence reference, and notes
- Log any exception as a ServiceNow Issue with an owner, remediation plan, and retest date

---

## Phase 7: ServiceNow IRM integration

Build out the ServiceNow governance layer and connect it to the AWS environment.

- Configure the Policy and Compliance module: Authority Documents for ISO 27001, SOC 2, and NIST CSF, with linked Control Objectives
- Set up the Risk Register
- Define GRC roles: control owner, risk manager, auditor, and admin
- Configure ServiceNow access control rules on the IRM tables to enforce least privilege and segregation of duties, so the person who raises or remediates an issue cannot be the one who closes it
- Build a Python integration against the ServiceNow Table API that pushes Security Hub findings as Issues, updates Compliance Assessment results from AWS Config's compliance state, and attaches evidence links from the S3 evidence store
- Add the segregation of duties configuration as a control in the Risk and Control Matrix, and test it by re-performance: create test users for each role, attempt restricted actions, and confirm correct allow and deny behaviour

---

## Phase 8: GRC reporting

Produce the dashboards a GRC stakeholder would actually look at.

- Build a metrics dashboard covering control effectiveness, risk exposure, and ongoing monitoring activity
- Source the underlying metrics from the AWS services already monitored in earlier phases: Config, Security Hub, GuardDuty, and CloudTrail
