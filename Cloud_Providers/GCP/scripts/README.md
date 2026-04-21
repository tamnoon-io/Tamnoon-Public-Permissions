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

## Interactive Mode

```bash
python3 tamnoon_onboarding.py
```

The script prompts for all required values with descriptions and validates input before proceeding.

### Example: Fresh Onboarding (Project Scope)

```
================================================================
         Tamnoon GCP Onboarding — Interactive Setup
================================================================

Authenticated as: admin@customer.com

Identity Project
  The GCP project where the Tamnoon service account, Workload Identity
  Pool, and Provider will be created. This can be any project in your
  organization (e.g., a shared infrastructure or security project).

Enter project ID: cust-shared-infra

No existing Tamnoon service account found in cust-shared-infra.
Proceeding with fresh onboarding.

Tamnoon Tenant ID
  Your Tamnoon tenant identifier (UUID format). This is provided by
  Tamnoon during onboarding and is used to establish the trust
  relationship between Tamnoon's AWS environment and your GCP project.

Enter tenant ID: 5104b7b7-56ee-4f51-97d8-0a6c49f846f5

Onboarding Scope
  Determines where the Tamnoon service account will receive IAM roles.
  Organization scope is recommended — it covers all current and future
  projects through IAM inheritance. Folder or project scope limits
  access to specific parts of your hierarchy.

  1. Organization (recommended — covers all projects)
  2. Folder (covers all projects within selected folders)
  3. Project (covers only the selected projects)

Enter choice [1-3]: 3

Project ID(s)
  The GCP project ID(s) to onboard. Only these specific projects
  will be covered. For multiple projects, separate with commas or spaces.

Enter project ID(s): cust-app-prod, cust-app-staging

API Enablement
  Tamnoon requires specific GCP APIs to be enabled on each project in
  scope (19 APIs including IAM, Cloud Asset, Logging, Compute, etc.).
  This step is safe to run — API enablement is idempotent.

Enable required APIs on target projects? [y/N] [N]: N

================================================================
         Tamnoon GCP Onboarding — Execution Plan
================================================================

Identity project:    cust-shared-infra
Tamnoon tenant ID:   5104b7b7-56ee-4f51-97d8-0a6c49f846f5
Scope:               Project
Targets:             cust-app-prod, cust-app-staging

Resources to create:
  1. Service account:  tamnoon-federate-svc-account@cust-shared-infra.iam.gserviceaccount.com
  2. WIF pool:         tamnoon-pool-federate
  3. WIF provider:     tamnoon-aws-federate (AWS 112665896816)
  4. WIF binding:      roles/iam.workloadIdentityUser
     Trusted role:     gcp-onboarding-trust-5104b7b7-56ee-4f51-97d8-0a6c49f846f5

Roles to assign (6):
  - roles/viewer
  - roles/browser
  - roles/iam.securityReviewer
  - roles/cloudasset.viewer
  - roles/logging.privateLogViewer
  - roles/serviceusage.serviceUsageConsumer

Proceed? [y/N]: y

[Step 1/5] Creating service account tamnoon-federate-svc-account...
  ✓ Created: tamnoon-federate-svc-account@cust-shared-infra.iam.gserviceaccount.com

[Step 2/5] Creating Workload Identity Pool tamnoon-pool-federate...
  ✓ Created: tamnoon-pool-federate

[Step 3/5] Creating AWS provider tamnoon-aws-federate...
  ✓ Created: tamnoon-aws-federate

[Step 4/5] Binding WIF principal to service account...
  Principal: principalSet://iam.googleapis.com/projects/482917305164/locations/global/workloadIdentityPools/tamnoon-pool-federate/attribute.aws_role/arn:aws:sts::112665896816:assumed-role/gcp-onboarding-trust-5104b7b7-56ee-4f51-97d8-0a6c49f846f5
  Role:      roles/iam.workloadIdentityUser
  Target:    tamnoon-federate-svc-account@cust-shared-infra.iam.gserviceaccount.com
  ✓ Binding created

[Step 5/5] Assigning 6 roles to 2 project(s)...
  [1/2] project cust-app-prod:
    ✓ roles/viewer
    ✓ roles/browser
    ✓ roles/iam.securityReviewer
    ✓ roles/cloudasset.viewer
    ✓ roles/logging.privateLogViewer
    ✓ roles/serviceusage.serviceUsageConsumer
  [2/2] project cust-app-staging:
    ✓ roles/viewer
    ✓ roles/browser
    ✓ roles/iam.securityReviewer
    ✓ roles/cloudasset.viewer
    ✓ roles/logging.privateLogViewer
    ✓ roles/serviceusage.serviceUsageConsumer

================================================================
ONBOARDING SUMMARY
  Service account:  tamnoon-federate-svc-account@cust-shared-infra.iam.gserviceaccount.com
  WIF pool:         tamnoon-pool-federate
  WIF provider:     tamnoon-aws-federate
  Roles assigned:   12/12

  All operations completed successfully.
================================================================

================================================================
ONBOARDING OUTPUT
Provide this JSON to Tamnoon to complete onboarding setup:
================================================================
{
  "identity_project_number": "482917305164",
  "service_account_id": "115283947201638492751",
  "workload_identity_pool_id": "tamnoon-pool-federate",
  "workload_identity_provider_id": "tamnoon-aws-federate"
}
================================================================
```

### Example: Expand Scope

```
================================================================
         Tamnoon GCP Onboarding — Interactive Setup
================================================================

Authenticated as: admin@customer.com

Identity Project
  ...

Enter project ID: cust-shared-infra

Existing Tamnoon onboarding detected:
  Service account:  tamnoon-federate-svc-account@cust-shared-infra.iam.gserviceaccount.com
  WIF pool:         tamnoon-pool-federate
  WIF provider:     tamnoon-aws-federate

Discovering current scope coverage...

Current scope:
  Project:      cust-app-prod
  Project:      cust-app-staging

What would you like to do?
  1. Expand scope (add projects, folders, or organization)
  2. Reduce scope (remove projects, folders, or organization)
  3. Offboarding (delete Tamnoon SA and associated WIF Pool and Provider)

Enter choice [1-3]: 1

  ...

Enter project ID(s): cust-app-prod, cust-data-warehouse

Skipping (already covered):
  cust-app-prod

Resources to add:
  cust-data-warehouse

Proceed? [y/N]: y

Assigning 6 roles to 1 project(s)...
  project cust-data-warehouse:
    ✓ roles/viewer
    ✓ roles/browser
    ✓ roles/iam.securityReviewer
    ✓ roles/cloudasset.viewer
    ✓ roles/logging.privateLogViewer
    ✓ roles/serviceusage.serviceUsageConsumer

================================================================
SCOPE EXPANSION SUMMARY
  Added:  1 project(s)
  Roles:  6/6
  All operations completed successfully.
================================================================
```

### Example: Offboarding

```
Existing Tamnoon onboarding detected:
  Service account:  tamnoon-federate-svc-account@cust-shared-infra.iam.gserviceaccount.com
  WIF pool:         tamnoon-pool-federate
  WIF provider:     tamnoon-aws-federate

Discovering current scope coverage...

Current scope:
  Project:      cust-app-prod
  Project:      cust-app-staging
  Project:      cust-data-warehouse

What would you like to do?
  1. Expand scope (add projects, folders, or organization)
  2. Reduce scope (remove projects, folders, or organization)
  3. Offboarding (delete Tamnoon SA and associated WIF Pool and Provider)

Enter choice [1-3]: 3

================================================================
  WARNING: This will delete the Tamnoon service account,
  Workload Identity Pool, Provider, and all IAM bindings.
================================================================

Proceed? [y/N]: y

[Step 1/4] Removing IAM role bindings...
  project cust-app-prod:
    ✓ roles/viewer removed
    ✓ roles/browser removed
    ...
  project cust-app-staging:
    ...
  project cust-data-warehouse:
    ...

[Step 2/4] Deleting WIF provider tamnoon-aws-federate...
  ✓ Deleted: tamnoon-aws-federate

[Step 3/4] Deleting WIF pool tamnoon-pool-federate...
  ✓ Deleted: tamnoon-pool-federate

[Step 4/4] Deleting service account tamnoon-federate-svc-account...
  ✓ Deleted: tamnoon-federate-svc-account@cust-shared-infra.iam.gserviceaccount.com

================================================================
OFFBOARDING SUMMARY
  Tamnoon onboarding fully removed.
================================================================
```

## CLI Mode

### Fresh onboarding

```bash
# Organization scope (recommended)
python3 tamnoon_onboarding.py \
    --identity-project cust-shared-infra \
    --tenant-id 5104b7b7-56ee-4f51-97d8-0a6c49f846f5 \
    --scope organization --org-id 123456789

# Project scope
python3 tamnoon_onboarding.py \
    --identity-project cust-shared-infra \
    --tenant-id 5104b7b7-56ee-4f51-97d8-0a6c49f846f5 \
    --scope project --project-ids proj-a proj-b

# Folder scope with optional API enablement and auto-approve
python3 tamnoon_onboarding.py \
    --identity-project cust-shared-infra \
    --tenant-id 5104b7b7-56ee-4f51-97d8-0a6c49f846f5 \
    --scope folder --folder-ids 111222333 444555666 \
    --enable-apis -y
```

### Expand scope

```bash
python3 tamnoon_onboarding.py \
    --identity-project cust-shared-infra \
    --expand --scope project --project-ids new-proj-a new-proj-b
```

### Reduce scope

```bash
python3 tamnoon_onboarding.py \
    --identity-project cust-shared-infra \
    --reduce --scope project --project-ids old-proj-a
```

### Offboarding

```bash
python3 tamnoon_onboarding.py \
    --identity-project cust-shared-infra --offboard
```

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
| `--enable-apis` | Enable required GCP APIs on target projects (optional) |
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
  "identity_project_number": "482917305164",
  "service_account_id": "115283947201638492751",
  "workload_identity_pool_id": "tamnoon-pool-federate",
  "workload_identity_provider_id": "tamnoon-aws-federate"
}
```

Provide this JSON to Tamnoon via the onboarding UI.
