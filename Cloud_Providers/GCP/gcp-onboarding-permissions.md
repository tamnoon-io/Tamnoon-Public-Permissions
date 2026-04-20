<img src="images/Tamnoon.png" width="470">

# Tamnoon Onboarding - GCP Permissions Reference

This document defines the GCP IAM roles assigned to the Tamnoon principal for investigation and analysis. All roles are read-only.

---

## 1. Prerequisites

### Operator Permissions

The onboarding is deployed via [Infrastructure Manager](https://cloud.google.com/infrastructure-manager/docs) using the [`tamnoon-io/gcp-onboarding`](https://github.com/tamnoon-io/gcp-onboarding) Terraform module. The Tamnoon UI generates a `gcloud infra-manager deployments apply` command that the customer's admin runs in Cloud Shell or a local terminal.

Two principals are involved — the **operator** (the human running the command) and the **acting service account** (passed via `--service-account`, which Infrastructure Manager impersonates to execute Terraform).

#### Operator (human running the gcloud command)

The operator triggers the Infrastructure Manager deployment and must be able to impersonate the acting service account.

**Option 1 — `roles/owner` + `roles/config.admin` on the identity project**

`roles/owner` covers API enablement, `iam.serviceAccounts.actAs`, and general project administration. `roles/config.admin` covers all Infrastructure Manager operations (`deployments apply` needs `create`, `get`, `update`, `lock`, `unlock`, `getState`, `updateState`, plus `revisions.get` and `revisions.list`).

**Option 2 — Least-privilege custom role on the identity project**

| Permission | Purpose |
|-----------|---------|
| `iam.serviceAccounts.create` | Create the acting service account (pre-requisite) |
| `resourcemanager.projects.setIamPolicy` | Grant roles to the acting SA (`roles/config.agent` + resource permissions) |
| `serviceusage.services.enable` | Enable the Infrastructure Manager API (`config.googleapis.com`) |
| `iam.serviceAccounts.actAs` | Impersonate the acting service account via `--service-account` |
| `config.deployments.create` | Create the Infrastructure Manager deployment |
| `config.deployments.get` | Check if deployment exists, read current state |
| `config.deployments.update` | Update existing deployment (scope expansion) |
| `config.deployments.getLock` | Read Terraform state lock |
| `config.deployments.lock` | Acquire state lock during apply |
| `config.deployments.unlock` | Release state lock |
| `config.deployments.getState` | Read Terraform state |
| `config.deployments.updateState` | Write Terraform state |
| `config.revisions.get` | Read revision output |
| `config.revisions.list` | List revisions |

> Alternatively, `roles/config.admin` can replace the `config.*` permissions, and `roles/iam.serviceAccountAdmin` can replace `iam.serviceAccounts.create`.

#### Acting Service Account (--service-account flag)

This is the service account that Infrastructure Manager impersonates to execute the Terraform module. It creates the actual GCP resources (service account, WIF pool/provider, IAM bindings). The Tamnoon UI asks for its fully qualified name (e.g., `projects/<project>/serviceAccounts/<sa-email>`).

The acting SA needs two categories of permissions: (a) `roles/config.agent` for Infrastructure Manager to manage Terraform state, logs, and storage; and (b) resource creation permissions for the Terraform module itself.

**Option 1 — `roles/owner` + `roles/config.agent` on the identity project + scope-appropriate IAM admin**

| Onboarding Scope | Acting SA Requirements |
|------------------|-----------------------|
| **Project** | `roles/config.agent` + `roles/owner` on the identity project |
| **Folder** | `roles/config.agent` + `roles/owner` on the identity project + `roles/resourcemanager.folderIamAdmin` on the target folder(s) |
| **Organization** | `roles/config.agent` + `roles/owner` on the identity project + `roles/resourcemanager.organizationAdmin` on the organization |

> **Why `roles/owner` alone is not enough for folder/org scope:** `roles/owner` includes `resourcemanager.projects.setIamPolicy` but does **not** include `resourcemanager.folders.setIamPolicy` or `resourcemanager.organizations.setIamPolicy`. Those permissions require a separate role at the target scope.

**Option 2 — Least-privilege custom role on the identity project**

| Permission | Purpose |
|-----------|---------|
| `roles/config.agent` (predefined) | Required by Infrastructure Manager — manages Terraform state, logs, Cloud Build, and storage for the deployment |
| `iam.serviceAccounts.create` | Create the Tamnoon service account |
| `iam.serviceAccounts.setIamPolicy` | Bind the WIF principal to the service account |
| `iam.googleapis.com/workloadIdentityPools.create` | Create the Workload Identity Federation pool |
| `iam.googleapis.com/workloadIdentityPoolProviders.create` | Create the AWS identity provider |
| `iam.roles.create` | Create the custom `TamnoonSecurityAssessment` role |
| `resourcemanager.projects.setIamPolicy` | Assign IAM roles at project level |

For folder or org scope, add the corresponding `setIamPolicy` permission at the target scope:
- **Folder**: `resourcemanager.folders.setIamPolicy` on each target folder
- **Organization**: `resourcemanager.organizations.setIamPolicy` on the organization

> **Scope expansion** — the acting SA only needs `roles/config.agent` and `resourcemanager.*.setIamPolicy` for new scope (the Tamnoon service account and WIF resources already exist). The operator still needs `config.*` permissions to trigger the deployment.

We strongly recommend Organization-level onboarding — it covers all GCP projects (existing and future) automatically through IAM inheritance.

### Tamnoon Principal

Tamnoon authenticates to customer GCP environments using a **dedicated service account** with **Workload Identity Federation (WIF)**. This eliminates long-lived credentials — Tamnoon's AWS workload assumes a federated identity that maps to the GCP service account, with no exported keys.

| Component | Value |
|-----------|-------|
| **Service Account** | `tamnoon-federate-service-account@<project-id>.iam.gserviceaccount.com` |
| **Authentication** | Workload Identity Federation (AWS → GCP) |
| **Trust Model** | A single AWS IAM role is authorized to impersonate the service account |

#### Infrastructure Deployment

The onboarding infrastructure is deployed via the [`tamnoon-io/gcp-onboarding`](https://github.com/tamnoon-io/gcp-onboarding) Terraform module through **GCP Infrastructure Manager**. The `config.googleapis.com` API must be enabled in the identity project.

The template creates the following resources:

| Resource | Purpose |
|----------|---------|
| **Service Account** (`tamnoon-federate-service-account`) | The principal that receives all IAM role bindings listed in [Section 2](#2-roles-assigned-to-tamnoon-service-account) |
| **Workload Identity Pool** | Federation endpoint that accepts external tokens |
| **Workload Identity Provider** (AWS) | Validates AWS STS tokens and extracts the caller's IAM role via attribute mapping |
| **WIF Principal Binding** | Grants `roles/iam.workloadIdentityUser` so the trusted AWS role can impersonate the service account |
| **IAM Role Bindings** | Assigns the 6 predefined roles (see [Section 2](#2-roles-assigned-to-tamnoon-service-account)) at the chosen scope |

The deployment supports three scoping modes:
- **Organization** (recommended) — set `organization_id`; roles are granted at org level and inherited by all projects
- **Folder** — provide `folder_ids` (semicolon-delimited); roles are granted per folder
- **Project** — provide `project_ids` (semicolon-delimited); roles are granted per project

#### Initial Onboarding and Scope Expansion

Both the initial deployment and scope expansion (adding new projects or folders) are handled through the Tamnoon onboarding workflow at [secure.tamnoon.io/settings/cloud/gcp/create](https://secure.tamnoon.io/settings/cloud/gcp/create). The workflow generates the appropriate `gcloud infra-manager deployments apply` command with pre-filled parameters.

For scope expansion, the same deployment is re-applied with updated `project_ids` or `folder_ids` — the service account and WIF resources remain unchanged, only new IAM bindings are added.

### Organization Policy Constraints

For GCP organizations created after May 3, 2024, the default organization policy restricts IAM access to your organization's domain only. To allow Tamnoon access, update one of the following constraints:

**Option 1 — Modern constraint: `iam.managed.allowedPolicyMembers` (Recommended)**

1. In the GCP Console, navigate to **IAM & Admin > Organization policies**
2. Search for **Allowed Policy Member Types** (ID: `constraints/iam.managed.allowedPolicyMembers`)
3. Click **Edit Policy** and add a rule (or edit existing)
4. Under **Custom Values**, add the Tamnoon principal

**Option 2 — Legacy constraint: `iam.allowedPolicyMemberDomains`**

1. In the GCP Console, navigate to **IAM & Admin > Organization policies**
2. Search for **Domain restricted sharing** (ID: `constraints/iam.allowedPolicyMemberDomains`)
3. Click **Edit Policy** and add a rule (or edit existing)
4. Configure the rule:
   - Policy values: **Custom**
   - Policy enforcement: **Allow**
   - Value: Add the Tamnoon Customer ID (provided during onboarding)
5. Verify your own organization's Customer ID is also present in an Allow rule to avoid locking out your own users
6. Click **Set policy**

---

## 2. Roles Assigned to Tamnoon Service Account

### Role Inventory

All roles are read-only. The table below explains what each role provides and the gap it fills.

| Role | Purpose | Why needed (gap it covers) |
|------|---------|----------------------------|
| `roles/viewer` | Read-only access to all resources, project-level IAM policies, recommender insights, policy analyzer | Base read access — but cannot navigate folder/org hierarchy, read folder/org IAM policies, access data access logs, or search assets across projects |
| `roles/browser` | Navigate organization, folder, and project hierarchy | `roles/viewer` cannot list folders (`folders.get`, `folders.list`) or view organization metadata (`organizations.get`). Required for hierarchy traversal in scripts |
| `roles/iam.securityReviewer` | Read IAM policies at all levels + SCC findings + security-relevant list permissions across all services (2,366 permissions) | `roles/viewer` only includes `projects.getIamPolicy` — it does **not** include `folders.getIamPolicy` or `organizations.getIamPolicy`. Also provides SCC access (`securitycenter.findings.list`, `securitycenter.assets.list`, `securitycenter.attackpaths.list`) — no separate SCC roles needed |
| `roles/cloudasset.viewer` | Bulk search IAM bindings and resources across the org | No other role provides cross-project IAM search. Required to discover where an identity (user, group, SA) has access beyond a single project — single API call returns all bindings org-wide |
| `roles/logging.privateLogViewer` | Read Data Access Logs and filtered log views | `roles/viewer` includes basic log reads but **not** data access audit logs (which record who accessed what data) |
| `roles/serviceusage.serviceUsageConsumer` | View enabled APIs and service usage quotas | `roles/viewer` does not include service usage permissions |

### Organization-Level Onboarding

Covers all GCP projects (existing and future) through IAM inheritance. Sections 2.2 and 2.3 are not applicable.

| Role | Purpose |
|------|---------|
| `roles/viewer` | Read-only access to all resources and project-level IAM policies |
| `roles/browser` | Navigate organization, folder, and project hierarchy |
| `roles/iam.securityReviewer` | Read IAM policies at organization, folder, and project levels |
| `roles/cloudasset.viewer` | Search IAM bindings and resources across all projects |
| `roles/logging.privateLogViewer` | Access Data Access Logs and filtered log views |
| `roles/serviceusage.serviceUsageConsumer` | View enabled APIs and service usage quotas |

### Folder-Level Onboarding

Applies when the customer decides not to onboard their entire GCP Organization. All projects within the specified folders are covered.

| Role | Purpose |
|------|---------|
| `roles/viewer` | Read-only access to all resources and project-level IAM policies |
| `roles/browser` | Navigate folder and project hierarchy |
| `roles/iam.securityReviewer` | Read IAM policies at folder and project levels |
| `roles/cloudasset.viewer` | Search IAM bindings and resources across folder scope |
| `roles/logging.privateLogViewer` | Access Data Access Logs and filtered log views |
| `roles/serviceusage.serviceUsageConsumer` | View enabled APIs and service usage quotas |

### Project-Level Onboarding

| Role | Purpose |
|------|---------|
| `roles/viewer` | Read-only access to all resources and project-level IAM policies |
| `roles/browser` | Navigate project hierarchy context |
| `roles/iam.securityReviewer` | Read project IAM policies + SCC findings within the project |
| `roles/cloudasset.viewer` | Search IAM bindings and resources within the project |
| `roles/logging.privateLogViewer` | Access Data Access Logs and filtered log views |
| `roles/serviceusage.serviceUsageConsumer` | View enabled APIs and service usage quotas |

**Note:** At project scope, `roles/browser`, `roles/iam.securityReviewer`, and `roles/cloudasset.viewer` are limited to the single project — they cannot see folder/org hierarchy or cross-project bindings. Organization-level onboarding is recommended for full coverage.

---

## 3. Scope-Level Capabilities

IAM roles are evaluated at the scope where they are granted. A role granted at project level cannot inspect resources at folder or organization levels.

| Capability | Project scope | Folder scope | Organization scope |
|------------|---------------|--------------|---------------------|
| Resource reads (Compute, Storage, IAM, etc.) | Project only | All projects in folder | All projects in org |
| Project IAM policy reads | Yes | Yes (inherited) | Yes (inherited) |
| Folder IAM policy reads | No | Yes | Yes |
| Organization IAM policy reads | No | No | Yes |
| Hierarchy navigation (folders, org) | No | Folder scope | Full org |
| Cross-project IAM binding search | No | Folder scope | Full org |
| Data access audit logs | Project only | All projects in folder | All projects in org |
| Deny policies, PAB, recommender insights | Project only | Folder scope | Full org |

---

## 4. Required APIs

The following GCP APIs must be enabled on each project in scope. APIs are grouped by category — not all are required for every engagement.

### Core (Required for all investigations)

| API | Service Name | Purpose |
|-----|-------------|---------|
| Cloud Resource Manager | `cloudresourcemanager.googleapis.com` | Project/folder/org hierarchy traversal and IAM policy reads |
| IAM | `iam.googleapis.com` | Service account metadata, key listing, role analysis |
| Cloud Logging | `logging.googleapis.com` | Audit logs, SA activity, request logs, impersonation detection |
| Cloud Asset | `cloudasset.googleapis.com` | Cross-project IAM binding and resource search |
| Policy Analyzer | `policyanalyzer.googleapis.com` | SA and key last authentication times (90d) |
| Recommender | `recommender.googleapis.com` | IAM policy recommendations and unused permission insights |
| Service Usage | `serviceusage.googleapis.com` | Detect which APIs are enabled per project |

### Compute & Networking

| API | Service Name | Purpose |
|-----|-------------|---------|
| Compute Engine | `compute.googleapis.com` | VM instances, firewall rules, load balancers, instance groups, serverless NEGs |

### Serverless

| API | Service Name | Purpose |
|-----|-------------|---------|
| Cloud Run Admin | `run.googleapis.com` | Cloud Run services, IAM policies, deployment metadata |
| Cloud Functions | `cloudfunctions.googleapis.com` | Cloud Functions (Gen1 + Gen2), IAM policies, triggers |
| Eventarc | `eventarc.googleapis.com` | Trigger detection for serverless upstream context |
| Pub/Sub | `pubsub.googleapis.com` | Push endpoint detection for serverless upstream context |
| API Gateway | `apigateway.googleapis.com` | API Gateway upstream auth context (OpenAPI spec inspection) |

### Data & Storage

| API | Service Name | Purpose |
|-----|-------------|---------|
| BigQuery | `bigquery.googleapis.com` | Log Analytics queries, BQ audit sink queries (extended history) |
| Cloud Storage | `storage.googleapis.com` | Bucket analysis (public access, versioning, IAM policies) |
| Cloud SQL Admin | `sqladmin.googleapis.com` | SQL instance configuration and flag analysis |
| Secret Manager | `secretmanager.googleapis.com` | Credential access for remediation scripts |

---

## 5. Custom Roles

### Tamnoon Security Assessment Role

The 6 predefined roles (Section 2) cover IAM investigation, audit log analysis, and resource enumeration. However, certain security assessment scenarios require permissions that no predefined read-only role provides. These are collected into a single custom role.

**Role name**: `TamnoonSecurityAssessment` (organization-level)

| Permission | Use Case | Why needed |
|------------|----------|------------|
| `container.secrets.get` | GKE credential exposure assessment | `roles/viewer` includes `container.secrets.list` (see secret names) but NOT `.get` (read secret data). Required to determine whether K8s secrets contain cleartext cloud credentials (SA keys, API tokens) — the core of "container with cleartext cloud keys" investigations |
| `artifactregistry.repositories.downloadArtifacts` | Container image scanning | Required to pull container images from Artifact Registry / GAR for layer-by-layer inspection. SA key JSON files baked into image layers during build are invisible from the running container filesystem — only detectable by scanning image layers |
| `storage.objects.get` | GCR image layer reads | GCR stores container image layers as objects in Cloud Storage buckets (`artifacts.PROJECT_ID.appspot.com`). Pulling an image from GCR requires reading these storage objects. Required alongside `artifactregistry.repositories.downloadArtifacts` for complete registry coverage (GCR + GAR) |

#### Investigation Scenarios

**Container with cleartext cloud keys granting high privileges**

A container image or K8s secret contains a GCP service account key (JSON with `"type": "service_account"` + `"private_key"`), and that SA has high-privilege roles. Investigation requires:

1. **List K8s secrets** (`container.secrets.list` — already in `roles/viewer`) — identify secrets mounted by the pod
2. **Read K8s secret data** (`container.secrets.get` — custom role) — determine if secrets contain SA key JSON or other cloud credentials
3. **Pull container image** (`artifactregistry.repositories.downloadArtifacts` + `storage.objects.get` — custom role) — scan image layers for embedded key files that may have been deleted in a later layer but remain in the image history
4. **Check SA privileges** (`cloudasset.viewer` — already assigned) — assess the blast radius of the exposed credentials

Without this custom role, Tamnoon can identify the workload (StatefulSet, Deployment), its Workload Identity binding, and the SA's IAM roles — but cannot verify whether cleartext credentials actually exist in secrets or image layers.

#### Creating the Custom Role

```bash
gcloud iam roles create TamnoonSecurityAssessment \
  --organization=ORGANIZATION_ID \
  --title="Tamnoon Security Assessment" \
  --description="Additional read permissions for security assessment scenarios (GKE secrets, container images, IaC state)" \
  --permissions=container.secrets.get,artifactregistry.repositories.downloadArtifacts,storage.objects.get \
  --stage=GA
```

Then assign to the Tamnoon principal:

```bash
gcloud organizations add-iam-policy-binding ORGANIZATION_ID \
  --member="user:tamnoonpoc@tamnoon.io" \
  --role="organizations/ORGANIZATION_ID/roles/TamnoonSecurityAssessment"
```

---

### Custom Logs Viewer (Fallback)

If `roles/logging.privateLogViewer` cannot be assigned, Tamnoon recommends creating the following custom role at the onboarding scope:

| Permission | Purpose |
|------------|---------|
| `logging.privateLogEntries.list` | Read data access and audit logs |
| `logging.views.access` | Access filtered log views |
| `logging.locations.get` | Read log storage location configuration |
| `logging.locations.list` | Enumerate available log storage regions |
| `resourcemanager.projects.get` | Read project metadata for log correlation |

`observability.scopes.get` is already included in `roles/viewer` and does not need to be added.

---

## 6. Summary

| Scope | Roles | Coverage |
|-------|-------|----------|
| **Organization** | 6 predefined roles + `TamnoonSecurityAssessment` custom role | Full — all resources, IAM policies at all levels, cross-project search, hierarchy navigation, data access logs, GKE secret inspection, container image scanning |
| **Folder** | 6 predefined roles + `TamnoonSecurityAssessment` custom role | Partial — folder and contained projects only |
| **Project** | 6 predefined roles + `TamnoonSecurityAssessment` custom role | Limited — same roles but scoped to single project only |

**Predefined roles**: `roles/viewer`, `roles/browser`, `roles/iam.securityReviewer`, `roles/cloudasset.viewer`, `roles/logging.privateLogViewer`, `roles/serviceusage.serviceUsageConsumer`

**Custom role**: `TamnoonSecurityAssessment` — GKE secret inspection (`container.secrets.get`), container image scanning (`artifactregistry.repositories.downloadArtifacts`, `storage.objects.get`)

---

## 7. SCC Coverage via Security Reviewer

`roles/iam.securityReviewer` includes 22 SCC permissions — sufficient for **investigation scripts** that discover and analyze findings:

| SCC Permission | Capability |
|----------------|------------|
| `securitycenter.findings.list` | List threat, vulnerability, and misconfiguration findings |
| `securitycenter.issues.list` | List SCC issues (grouped findings) |
| `securitycenter.assets.list` | List SCC asset inventory |
| `securitycenter.attackpaths.list` | List attack path simulations |
| `securitycenter.sources.list` | List SCC finding sources |

### What `iam.securityReviewer` does NOT include

The following SCC permissions require `roles/securitycenter.findingsViewer` (which is a superset of `roles/securitycenter.issuesViewer` — never grant both):

| Permission | Capability | When needed |
|------------|-----------|-------------|
| `securitycenter.issues.get` | Fetch a specific Issue by ID | Programmatic SCC alert ingestion |
| `securitycenter.findings.group` | Aggregate findings by category/severity | Dashboard / reporting |
| `securitycenter.findingexplanations.get` | SCC AI-generated finding explanations | Enriched alert context |
| `securitycenter.graphs.get` / `.query` | Attack graph traversal | Finding correlation |
| `securitycenter.issues.group` / `.listFilterValues` | Issue aggregation and filter discovery | Issue-level analytics |

### When to use which role

| Use Case | Role | Scope |
|----------|------|-------|
| **Investigation scripts** (`--csv-input` driven) | `roles/iam.securityReviewer` (already in onboarding) | Org / Folder / Project |
| **SCC alert ingestion** (Tamnoon Alerts page) | `roles/securitycenter.findingsViewer` (add to the same SA) | Org or Project (SCC doesn't support folder-level activation) |

**Legacy onboarding** (current): `tamnoonpoc@tamnoon.io` user account — add `findingsViewer` to the same user for SCC ingestion.

**SA-based onboarding** (May 2026+): A single SA handles both investigation and SCC ingestion. Grant both the onboarding roles and `findingsViewer` — they are additive with minimal overlap.

See [SCC Integration](gcp-scc-integration.md) for setup details.

---

## 8. Optional Integrations

| Integration | Purpose | Configuration | Doc |
|-------------|---------|---------------|-----|
| **Google Workspace** | Enrich user/group investigations with identity context (name, OU, status, group membership) | Domain-wide delegation with Admin SDK read-only scopes | [Workspace Integration](gcp-workspace-integration.md) |
| **SCC Alert Ingestion** | Programmatic ingestion of SCC findings into Tamnoon Alerts page | Dedicated SA with `findingsViewer` at org or project scope | [SCC Integration](gcp-scc-integration.md) |

**Note**: Workspace and SCC Alert Ingestion are the only integrations that require configuration beyond the standard onboarding roles. For investigation scripts, SCC access is already covered by `roles/iam.securityReviewer` at org/folder scope.
