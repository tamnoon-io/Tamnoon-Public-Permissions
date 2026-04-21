<img src="../images/Tamnoon.png" width="470">

# GCP Onboarding Script

Python script to onboard, manage, and offboard the Tamnoon service account with Workload Identity Federation (WIF) in Google Cloud. Alternative to deploying the [`tamnoon-io/gcp-onboarding`](https://github.com/tamnoon-io/gcp-onboarding) Terraform module via Infrastructure Manager.

## Prerequisites

- **Python 3.x** and **gcloud CLI** (pre-installed in Google Cloud Shell)
- Authenticated with `gcloud auth login`
- Permissions depend on the operation (see [Operator Permissions](#operator-permissions))

## Operations

| Operation | Description |
|-----------|-------------|
| **Fresh onboarding** | Create the Tamnoon service account, WIF pool/provider, and assign IAM roles at the chosen scope |
| **Expand scope** | Add new projects, folders, or organization to an existing onboarding |
| **Reduce scope** | Remove projects, folders, or organization from an existing onboarding |
| **Offboarding** | Delete the Tamnoon service account, WIF pool/provider, and all IAM bindings |

The script auto-detects the operation mode: if the Tamnoon service account (`tamnoon-federate-svc-account`) already exists in the identity project, it presents the expand/reduce/offboard menu. Otherwise, it proceeds with fresh onboarding.

## Usage

### Interactive mode

```bash
python3 tamnoon_onboarding.py
```

The script prompts for all required values with descriptions and validates input before proceeding.

### CLI mode — Fresh onboarding

```bash
# Organization scope (recommended)
python3 tamnoon_onboarding.py \
    --identity-project my-infra-project \
    --tenant-id 5104b7b7-56ee-4f51-97d8-0a6c49f846f5 \
    --scope organization --org-id 123456789

# Project scope
python3 tamnoon_onboarding.py \
    --identity-project my-infra-project \
    --tenant-id 5104b7b7-56ee-4f51-97d8-0a6c49f846f5 \
    --scope project --project-ids proj-a proj-b

# Folder scope with API enablement and auto-approve
python3 tamnoon_onboarding.py \
    --identity-project my-infra-project \
    --tenant-id 5104b7b7-56ee-4f51-97d8-0a6c49f846f5 \
    --scope folder --folder-ids 111222333 444555666 \
    --enable-apis -y
```

### CLI mode — Expand scope

```bash
# Add new projects
python3 tamnoon_onboarding.py \
    --identity-project my-infra-project \
    --expand --scope project --project-ids new-proj-a new-proj-b

# Add organization scope
python3 tamnoon_onboarding.py \
    --identity-project my-infra-project \
    --expand --scope organization --org-id 123456789
```

The script discovers current coverage and skips resources that are already onboarded.

### CLI mode — Reduce scope

```bash
# Remove specific projects
python3 tamnoon_onboarding.py \
    --identity-project my-infra-project \
    --reduce --scope project --project-ids old-proj-a

# Remove folder
python3 tamnoon_onboarding.py \
    --identity-project my-infra-project \
    --reduce --scope folder --folder-ids 111222333
```

The script discovers current coverage and skips resources that don't have existing bindings.

### CLI mode — Offboarding

```bash
python3 tamnoon_onboarding.py \
    --identity-project my-infra-project --offboard
```

Discovers all existing IAM bindings, removes them, then deletes the WIF provider, WIF pool, and service account.

## Options

| Option | Description |
|--------|-------------|
| `--identity-project` | GCP project ID where the SA and WIF resources are created |
| `--tenant-id` | Tamnoon tenant ID — UUID provided during onboarding (fresh onboarding only) |
| `--scope` | Scope level: `organization`, `folder`, or `project` |
| `--org-id` | Organization ID (for organization scope) |
| `--folder-ids` | One or more folder IDs (for folder scope) |
| `--project-ids` | One or more project IDs (for project scope) |
| `--expand` | Expand scope — add resources to existing onboarding |
| `--reduce` | Reduce scope — remove resources from existing onboarding |
| `--offboard` | Delete Tamnoon SA, WIF Pool, Provider, and all IAM bindings |
| `--enable-apis` | Enable required GCP APIs on target projects |
| `-y, --yes` | Skip confirmation prompt |

## What the Script Creates

| Resource | Name | Description |
|----------|------|-------------|
| Service Account | `tamnoon-federate-svc-account` | The Tamnoon principal that receives IAM roles |
| Workload Identity Pool | `tamnoon-pool-federate` | Federation endpoint that accepts external tokens |
| Workload Identity Provider | `tamnoon-aws-federate` | AWS provider with attribute condition scoped to the Tamnoon tenant |
| WIF Principal Binding | `roles/iam.workloadIdentityUser` | Allows the trusted AWS role to impersonate the service account |
| IAM Role Bindings | 6 predefined roles | Assigned at the chosen scope (see below) |

## Roles Assigned

| Role | Purpose |
|------|---------|
| `roles/viewer` | Read-only access to all resources and project-level IAM policies |
| `roles/browser` | Navigate organization, folder, and project hierarchy |
| `roles/iam.securityReviewer` | Read IAM policies at all levels + SCC findings |
| `roles/cloudasset.viewer` | Search IAM bindings and resources across projects |
| `roles/logging.privateLogViewer` | Access Data Access Logs and filtered log views |
| `roles/serviceusage.serviceUsageConsumer` | View enabled APIs and service usage quotas |

See [gcp-onboarding-permissions.md](../gcp-onboarding-permissions.md#2-roles-assigned-to-tamnoon-service-account) for detailed justification of each role.

## Operator Permissions

The operator running this script needs different permissions depending on the operation:

### Fresh onboarding

| Permission | Purpose |
|-----------|---------|
| `iam.serviceAccounts.create` | Create the Tamnoon service account |
| `iam.serviceAccounts.get` | Verify SA exists (idempotency check) |
| `iam.serviceAccounts.setIamPolicy` | Bind the WIF principal to the SA |
| `iam.googleapis.com/workloadIdentityPools.create` | Create the WIF pool |
| `iam.googleapis.com/workloadIdentityPools.get` | Verify pool exists (idempotency check) |
| `iam.googleapis.com/workloadIdentityPoolProviders.create` | Create the AWS provider |
| `iam.googleapis.com/workloadIdentityPoolProviders.get` | Verify provider exists (idempotency check) |
| `resourcemanager.projects.get` | Read project number for WIF binding |
| `resourcemanager.{projects\|folders\|organizations}.setIamPolicy` | Assign IAM roles at the chosen scope |

### Expand / Reduce scope

| Permission | Purpose |
|-----------|---------|
| `cloudasset.assets.searchAllIamPolicies` | Discover current scope coverage |
| `resourcemanager.{projects\|folders\|organizations}.setIamPolicy` | Add or remove IAM role bindings |

### Offboarding

| Permission | Purpose |
|-----------|---------|
| `cloudasset.assets.searchAllIamPolicies` | Discover all existing IAM bindings |
| `resourcemanager.{projects\|folders\|organizations}.setIamPolicy` | Remove IAM role bindings |
| `iam.googleapis.com/workloadIdentityPoolProviders.delete` | Delete the WIF provider |
| `iam.googleapis.com/workloadIdentityPools.delete` | Delete the WIF pool |
| `iam.serviceAccounts.delete` | Delete the service account |

### API enablement (optional)

| Permission | Purpose |
|-----------|---------|
| `serviceusage.services.enable` | Enable required APIs on target projects |

See [gcp-onboarding-permissions.md](../gcp-onboarding-permissions.md#1-prerequisites) for full permission details including predefined role alternatives.

## Output

After fresh onboarding, the script prints a JSON block that Tamnoon needs to complete the onboarding setup:

```json
{
  "identity_project_number": "847291035612",
  "service_account_id": "108753514435471618950",
  "workload_identity_pool_id": "tamnoon-pool-federate",
  "workload_identity_provider_id": "tamnoon-aws-federate"
}
```

Provide this JSON to Tamnoon via the onboarding UI.
