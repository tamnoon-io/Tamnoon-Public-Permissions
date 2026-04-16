<img src="images/Tamnoon.png" width="470">

# GCP Security Command Center Integration

This document defines the permissions needed for Tamnoon to ingest SCC findings into the Tamnoon Alerts page. This is separate from the standard onboarding ([gcp-onboarding-permissions.md](gcp-onboarding-permissions.md)) which covers investigation scripts.

---

## 1. Prerequisites

### SCC Activation

SCC must be activated before the integration has anything to ingest. SCC supports activation at **Organization** or **Project** scope only — folder-level SCC activation is not supported ([reference](https://cloud.google.com/security-command-center/docs/activate-scc-overview)).

| SCC Tier | Where SCC can be activated |
|---|---|
| Standard | Organization OR Project |
| Premium | Organization OR Project |
| Enterprise | Organization only |

Verify activation:
```bash
# Org-level
gcloud scc settings services list --organization=ORG_ID

# Project-level
gcloud scc settings services list --project=PROJECT_ID
```

### Operator Permissions

The person performing the setup needs:

**To create the service account** (on the tenant project where the SA lives):

| Task | Role |
|---|---|
| Create the SA | `roles/iam.serviceAccountAdmin` |
| Set IAM policy on the SA (required for WIF / impersonation) | `roles/iam.serviceAccountAdmin` |
| Create WIF pool & provider (recommended over keys) | `roles/iam.workloadIdentityPoolAdmin` |

**To grant the SA `findingsViewer`** at the SCC activation scope:

| Integration Scope | Operator Requirement |
|---|---|
| **Organization** | `roles/resourcemanager.organizationAdmin` OR `roles/iam.securityAdmin` at org |
| **Project(s)** | `roles/resourcemanager.projectIamAdmin` OR `roles/owner` on each project |

---

## 2. Tamnoon Principal

### Legacy onboarding (current)

Customers onboarded before May 2026 use the **Tamnoon user account** (`tamnoonpoc@tamnoon.io`). For SCC integration on legacy onboarding, grant `findingsViewer` to the existing user:

```bash
gcloud organizations add-iam-policy-binding ORG_ID \
  --member="user:tamnoonpoc@tamnoon.io" \
  --role="roles/securitycenter.findingsViewer" \
  --condition=None
```

### Service Account onboarding (May 2026+)

Starting May 2026, Tamnoon uses a **single service account** for both investigation and SCC alert ingestion. If the onboarding SA already exists, add `findingsViewer` to it — do not create a separate SA.

**Existing SA** (onboarding already done):
```bash
SA="serviceAccount:tamnoon-sa@TENANT_PROJECT.iam.gserviceaccount.com"

gcloud organizations add-iam-policy-binding ORG_ID \
  --member="$SA" \
  --role="roles/securitycenter.findingsViewer" \
  --condition=None
```

**New customer** (onboarding + SCC integration from day one):
```bash
gcloud iam service-accounts create tamnoon-sa \
  --display-name="Tamnoon Security Engineering" \
  --project=TENANT_PROJECT
```
Then grant both the [onboarding roles](gcp-onboarding-permissions.md#2-roles-assigned-to-tamnoon) AND `findingsViewer` (Section 4 below).

**Authentication**: Workload Identity Federation (recommended) or Service Account Key (legacy).

---

## 3. Role Assigned to the SA

| Role | Purpose |
|---|---|
| `roles/securitycenter.findingsViewer` | List and retrieve SCC findings and issues |

**Why this role**: `findingsViewer` is a superset of `issuesViewer` — do not grant both. It provides:

- `securitycenter.findings.list`, `findings.group`, `findings.listFindingPropertyNames`
- `securitycenter.issues.list`, `issues.get`, `issues.group`, `issues.listFilterValues`
- `securitycenter.findingexplanations.get`
- `securitycenter.graphs.get`, `graphs.query`
- `securitycenter.sources.list`, `sources.get`
- `securitycenter.compliancesnapshots.list`, `vulnerabilitysnapshots.list`
- `resourcemanager.folders.get`, `organizations.get`, `projects.get`

---

## 4. Integration Scope — Grant Commands

Grant `findingsViewer` at a scope that covers all projects where SCC is activated.

### 4.1 Organization-Level (Recommended)

```bash
SA="serviceAccount:tamnoon-scc-integration@TENANT_PROJECT.iam.gserviceaccount.com"

gcloud organizations add-iam-policy-binding ORG_ID \
  --member="$SA" \
  --role="roles/securitycenter.findingsViewer" \
  --condition=None
```

Coverage: All current and future projects in the organization.

### 4.2 Project-Level (Multiple Projects)

Use when SCC is activated per-project (Standard/Premium without org-level activation).

```bash
SA="serviceAccount:tamnoon-scc-integration@TENANT_PROJECT.iam.gserviceaccount.com"

for PROJECT in project-a project-b project-c; do
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="$SA" \
    --role="roles/securitycenter.findingsViewer" \
    --condition=None
done
```

Or from a file (one project ID per line):

```bash
while IFS= read -r PROJECT; do
  [[ -z "$PROJECT" || "$PROJECT" =~ ^# ]] && continue
  gcloud projects add-iam-policy-binding "$PROJECT" \
    --member="$SA" \
    --role="roles/securitycenter.findingsViewer" \
    --condition=None
done < projects.txt
```

**Limitations of project-level**:
- No cross-project attack paths
- No org-wide asset inventory correlation
- Must re-run when new projects activate SCC

---

## 5. Quota Project

The SCC API requires a quota project with `securitycenter.googleapis.com` enabled:

```bash
gcloud projects add-iam-policy-binding TENANT_PROJECT \
  --member="$SA" \
  --role="roles/serviceusage.serviceUsageConsumer" \
  --condition=None
```

Use `--billing-project=TENANT_PROJECT` in gcloud commands or `x-goog-user-project` header for REST calls.

---

## 6. Verification

```bash
# Check role binding
gcloud organizations get-iam-policy ORG_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:tamnoon-scc-integration" \
  --format="table(bindings.role)"

# Test finding access
gcloud scc findings list organizations/ORG_ID \
  --location=global \
  --impersonate-service-account=tamnoon-scc-integration@TENANT_PROJECT.iam.gserviceaccount.com \
  --filter='state="ACTIVE"' \
  --limit=5
```

---

## 7. Relationship to Standard Onboarding

### Legacy onboarding (user-based)

| Principal | Onboarding roles | SCC integration | Status |
|-----------|-----------------|-----------------|--------|
| `tamnoonpoc@tamnoon.io` | 6 predefined + `TamnoonSecurityAssessment` | Add `findingsViewer` to same user | Current |

### SA-based onboarding (May 2026+)

A **single SA** handles both investigation and SCC ingestion. The roles are additive with minimal overlap (`findings.list` and `issues.list` are duplicated, which is harmless).

| Source | Roles |
|--------|-------|
| [Standard onboarding](gcp-onboarding-permissions.md) | `roles/viewer`, `roles/browser`, `roles/iam.securityReviewer`, `roles/cloudasset.viewer`, `roles/logging.privateLogViewer`, `roles/serviceusage.serviceUsageConsumer`, `TamnoonSecurityAssessment` (custom) |
| SCC integration (**this doc**) | `roles/securitycenter.findingsViewer` |

### What each part provides

| Capability | Provided by |
|-----------|------------|
| List findings for investigation scripts | `iam.securityReviewer` (onboarding) |
| Fetch individual Issues by ID | `findingsViewer` (this doc) |
| Finding aggregation, explanations, graph queries | `findingsViewer` (this doc) |
| Read resources, IAM policies, audit logs | Onboarding roles |
| GKE secrets, container image scanning | `TamnoonSecurityAssessment` (onboarding) |

---

## 8. What Tamnoon Ingests

| SCC Data Type | Usage |
|---------------|-------|
| **Threat findings** (active) | Correlate with IAM bindings — which identities have access to affected resources |
| **Vulnerability findings** | Prioritize remediation based on exposure (network access + IAM scope) |
| **Misconfiguration findings** | Surface compliance gaps (open ports, public access, key rotation) |
| **Issues** (grouped findings) | Aggregate related findings for investigation prioritization |
| **Attack paths** | Understand lateral movement risk through IAM role chains |

See also:
- [GCP Onboarding Permissions](gcp-onboarding-permissions.md) — standard IAM investigation roles
- [Google Workspace Integration](gcp-workspace-integration.md) — identity enrichment for user/group investigations
