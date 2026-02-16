<img src="images/Tamnoon.png" width="470">

# Tamnoon Onboarding - GCP Permissions Reference

This document defines the GCP IAM roles assigned to the Tamnoon principal for investigation and analysis. All roles are read-only.

---

## 1. Prerequisites

### Operator Permissions

The user performing the onboarding must have sufficient permissions to assign IAM roles at the target scope.

| Onboarding Scope | Operator Requirements |
|------------------|-----------------------|
| **Organization** | GCP Organization Owner, or a user with `roles/iam.serviceAccountAdmin`, `roles/iam.organizationRoleAdmin`, `roles/iam.securityAdmin` at org level |
| **Project** | GCP Project Owner (or higher) |

We strongly recommend Organization-level onboarding — it covers all GCP projects (existing and future) automatically through IAM inheritance.

### Tamnoon Principal

| Principal | Type | Status | Capabilities |
|-----------|------|--------|-------------|
| `tamnoonpoc@tamnoon.io` | User | Current | GCP IAM, SCC, Cloud Asset API |
| TBD | Service Account (workload identity federation) | Planned | All current + Workspace Admin SDK (domain-wide delegation) |

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

## 2. Roles Assigned to Tamnoon

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
| `storage.objects.get` | GCR image pull + IaC state file inspection | GCR stores images as Cloud Storage objects. Also enables reading Terraform state files to understand how resources were provisioned and map infrastructure-as-code to live resources |

#### Investigation Scenarios

**Container with cleartext cloud keys granting high privileges**

A container image or K8s secret contains a GCP service account key (JSON with `"type": "service_account"` + `"private_key"`), and that SA has high-privilege roles. Investigation requires:

1. **List K8s secrets** (`container.secrets.list` — already in `roles/viewer`) — identify secrets mounted by the pod
2. **Read K8s secret data** (`container.secrets.get` — custom role) — determine if secrets contain SA key JSON or other cloud credentials
3. **Pull container image** (`artifactregistry.repositories.downloadArtifacts` + `storage.objects.get` — custom role) — scan image layers for embedded key files that may have been deleted in a later layer but remain in the image history
4. **Check SA privileges** (`cloudasset.viewer` — already assigned) — assess the blast radius of the exposed credentials

Without this custom role, Tamnoon can identify the workload (StatefulSet, Deployment), its Workload Identity binding, and the SA's IAM roles — but cannot verify whether cleartext credentials actually exist in secrets or image layers.

**Terraform state file analysis**

Terraform state files (typically in Cloud Storage) contain the full mapping of IaC declarations to live resources, including resource IDs, configurations, and sometimes sensitive outputs. `storage.objects.get` enables reading these files to understand provisioning context during investigations.

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

**Custom role**: `TamnoonSecurityAssessment` — `container.secrets.get`, `artifactregistry.repositories.downloadArtifacts`, `storage.objects.get`

---

## 7. SCC Coverage via Security Reviewer

`roles/iam.securityReviewer` includes 22 SCC permissions — no separate SCC roles needed for standard use:

| SCC Permission | Capability |
|----------------|------------|
| `securitycenter.findings.list` | List threat, vulnerability, and misconfiguration findings |
| `securitycenter.assets.list` | List SCC asset inventory |
| `securitycenter.attackpaths.list` | List attack path simulations |
| `securitycenter.sources.list` | List SCC finding sources |

**When separate SCC roles ARE still needed**: If Tamnoon is onboarded at **project level** (no `roles/iam.securityReviewer`), or if SCC is activated at folder level and the customer needs granular SCC role control. See [SCC Integration](gcp-scc-integration.md) for folder-level role details.

---

## 8. Optional Integrations

| Integration | Purpose | Configuration | Doc |
|-------------|---------|---------------|-----|
| **Google Workspace** | Enrich user/group investigations with identity context (name, OU, status, group membership) | Domain-wide delegation with Admin SDK read-only scopes | [Workspace Integration](gcp-workspace-integration.md) |

**Note**: Workspace is the only integration that requires configuration beyond the standard onboarding roles. SCC access is already covered by `roles/iam.securityReviewer` at org/folder scope.
