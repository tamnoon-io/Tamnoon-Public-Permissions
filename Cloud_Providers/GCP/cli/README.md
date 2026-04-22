<img src="../images/Tamnoon.png" width="470">

# GCP Onboarding — CLI Reference

Raw `gcloud` commands for onboarding the Tamnoon service account with Workload Identity Federation (WIF). Use this when you prefer copy-paste CLI commands over the interactive Python script or Infrastructure Manager deployment.

## Deployment Options

| Option | Location | Best for |
|--------|----------|----------|
| **Infrastructure Manager** | [Tamnoon UI](https://secure.tamnoon.io/settings/cloud/gcp/create) generates the command | Customers using the Tamnoon platform |
| **Python script** | [`scripts/tamnoon_onboarding.py`](../scripts/) | Interactive onboarding with scope management (expand/reduce/offboard) |
| **Terraform module** | [`tamnoon-io/gcp-onboarding`](https://github.com/tamnoon-io/gcp-onboarding) | Customers with existing Terraform workflows |
| **CLI commands** | [`gcloud_onboarding.md`](gcloud_onboarding.md) | Copy-paste `gcloud` commands for manual execution |

## Prerequisites

- **gcloud CLI** authenticated (`gcloud auth login`)
- Run from **Google Cloud Shell** or any environment with gcloud installed

### Operator Permissions

| Permission | Purpose |
|-----------|---------|
| `iam.serviceAccounts.create` | Create the Tamnoon service account |
| `iam.serviceAccounts.get` | Verify SA exists |
| `iam.serviceAccounts.setIamPolicy` | Bind the WIF principal to the SA |
| `iam.googleapis.com/workloadIdentityPools.create` | Create the WIF pool |
| `iam.googleapis.com/workloadIdentityPoolProviders.create` | Create the AWS provider |
| `resourcemanager.projects.get` | Read project number for WIF binding |
| `resourcemanager.{projects\|folders\|organizations}.setIamPolicy` | Assign IAM roles at the chosen scope |

See [gcp-onboarding-permissions.md](../gcp-onboarding-permissions.md#1-prerequisites) for full details including predefined role alternatives.

## Commands

See [gcloud_onboarding.md](gcloud_onboarding.md) for the step-by-step commands:

1. Create Service Account (`tamnoon-federate-svc-account`)
2. Create Workload Identity Pool (`tamnoon-pool-federate`)
3. Create AWS Provider (`tamnoon-aws-federate`)
4. Bind WIF Principal to Service Account
5. Assign IAM Roles at Scope (organization, folder, or project)
6. Retrieve Onboarding Output (JSON for Tamnoon UI)

## Values You Need

| Value | Where to get it |
|-------|----------------|
| **Identity project ID** | Any GCP project in your org (e.g., shared infra project) |
| **Tamnoon tenant ID** | Provided by Tamnoon during onboarding (UUID) |
| **Onboarding scope** | Organization ID, folder ID(s), or project ID(s) |

### Fixed Values (do not change)

| Value | Description |
|-------|-------------|
| `112665896816` | Tamnoon AWS account ID |
| `tamnoon-federate-svc-account` | Service account name |
| `tamnoon-pool-federate` | WIF pool ID |
| `tamnoon-aws-federate` | WIF provider ID |
| `gcp-onboarding-trust-<tenant-id>` | Trusted AWS role name pattern |
