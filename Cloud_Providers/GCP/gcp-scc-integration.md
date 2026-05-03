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

## 3. Roles Assigned to the SA

### 3.1 SCC Findings Ingestion

| Role | Purpose |
|---|---|
| `roles/securitycenter.findingsViewer` | List and retrieve SCC findings, issues, graphs, and explanations |

`findingsViewer` is a superset of `issuesViewer` — do not grant both. It provides:

- `securitycenter.findings.list`, `findings.group`, `findings.listFindingPropertyNames`
- `securitycenter.issues.list`, `issues.get`, `issues.group`, `issues.listFilterValues`
- `securitycenter.findingexplanations.get`
- `securitycenter.graphs.get`, `graphs.query`
- `securitycenter.sources.list`, `sources.get`
- `securitycenter.compliancesnapshots.list`, `vulnerabilitysnapshots.list`
- `resourcemanager.folders.get`, `organizations.get`, `projects.get`

### 3.2 SCC Investigation (Attack Paths, Valued Resources, Simulations)

The following roles are required when the CNAPP is GCP SCC and Tamnoon needs to investigate CHOKEPOINT and TOXIC_COMBINATION findings. These APIs **only support organization-level access** — project or folder-scoped grants will not work.

| Role | Title | Permissions | Why needed |
|------|-------|------------|-----------|
| `roles/securitycenter.attackPathsViewer` | Attack Paths Reader | `securitycenter.attackpaths.list`, `securitycenter.exposurepathexplan.get` | Read step-by-step attack chains — the actual resources in the attack path |
| `roles/securitycenter.valuedResourcesViewer` | Valued Resources Reader | `securitycenter.valuedresources.list` | Identify which specific resources SCC considers "valued" (the targets in "Function that exposes many valued resources") |
| `roles/securitycenter.simulationsViewer` | Simulations Reader | `securitycenter.simulations.get` | Read simulation context and metadata for attack exposure analysis |

> **Why `findingsViewer` alone is insufficient:** The findings list endpoint (`/v2/organizations/{org}/sources/-/findings`) returns the finding with an `attackExposure.score` and resource counts (e.g., 26 high-value, 8 medium-value), but does NOT return which resources are exposed or the attack chain. That data requires the separate attack paths, valued resources, and simulations APIs listed above.

### 3.3 SCC Investigation (Mute Rules, Detection Modules, Notifications)

When investigating SCC findings, Tamnoon scripts detect inconsistencies between mute rules and actual data flows (e.g., a mute rule suppresses "dev" BQ exports but the exported data originates from production). Reading mute rule definitions and detection configurations requires additional permissions.

| Permission | Why needed |
|-----------|-----------|
| `securitycenter.muteconfigs.list` | List all mute rules to identify suppressed findings |
| `securitycenter.muteconfigs.get` | Read mute rule filter to verify scope matches intent |
| `securitycenter.eventthreatdetectioncustommodules.list` | List custom ETD detection rules — check if customer has custom rules for exfiltration patterns |
| `securitycenter.notificationconfig.list` | List SCC notification routing — verify findings are routed to the right team (not just muted) |

**Predefined role:** `roles/securitycenter.adminViewer` includes all of the above.

**Scope:** Organization-level (mute rules and ETD modules are org-scoped).

> **Why `findingsViewer` is insufficient:** The `mute` and `muteInitiator` fields in finding JSON tell us a finding IS muted and by WHICH rule, but not the rule's filter definition. Without `muteconfigs.get`, we can infer the rule name from `muteInitiator` but cannot verify the filter matches the intended scope — critical for detecting suppressed production data exfiltration.

### Least-privilege custom role alternative

If the customer prefers a single custom role instead of the predefined roles:

```yaml
title: TamnoonSCCReader
description: Read-only SCC access for findings ingestion and investigation
permissions:
  # Findings ingestion
  - securitycenter.findings.list
  - securitycenter.findings.group
  - securitycenter.findings.listFindingPropertyNames
  - securitycenter.findingexplanations.get
  - securitycenter.issues.list
  - securitycenter.issues.get
  - securitycenter.issues.group
  - securitycenter.issues.listFilterValues
  - securitycenter.sources.list
  - securitycenter.sources.get
  - securitycenter.graphs.get
  - securitycenter.graphs.query
  - securitycenter.compliancesnapshots.list
  - securitycenter.vulnerabilitysnapshots.list
  - securitycenter.complianceReports.aggregate
  - securitycenter.userinterfacemetadata.get
  # Attack path investigation
  - securitycenter.attackpaths.list
  - securitycenter.exposurepathexplan.get
  - securitycenter.valuedresources.list
  - securitycenter.simulations.get
  # Mute rules, detection config, notifications
  - securitycenter.muteconfigs.list
  - securitycenter.muteconfigs.get
  - securitycenter.eventthreatdetectioncustommodules.list
  - securitycenter.notificationconfig.list
  # Resource hierarchy
  - resourcemanager.organizations.get
  - resourcemanager.folders.get
  - resourcemanager.projects.get
```

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

> **Organization-level is required.** SCC attack path, valued resource, and simulation APIs only support organization-scoped access. Project-level bindings cannot query these APIs, which limits the value of SCC findings to basic alerts without attack chain context.

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
| List attack paths (step-by-step attack chains) | `attackPathsViewer` (this doc) |
| List valued resources (exposed targets) | `valuedResourcesViewer` (this doc) |
| Read simulation context | `simulationsViewer` (this doc) |
| Read mute rule definitions | `muteconfigs.list/get` (section 3.3) |
| Detect suppressed findings with inconsistent scope | `muteconfigs.get` (section 3.3) |
| List custom ETD detection rules | `eventthreatdetectioncustommodules.list` (section 3.3) |
| Read notification routing | `notificationconfig.list` (section 3.3) |
| Read resources, IAM policies, audit logs | Onboarding roles |
| GKE secrets, container image scanning | `TamnoonSecurityAssessment` (onboarding) |

---

## 8. What Tamnoon Ingests

| SCC Data Type | Usage | API Endpoint |
|---------------|-------|-------------|
| **Threat findings** (active) | Correlate with IAM bindings — which identities have access to affected resources | `findings.list` |
| **Vulnerability findings** | Prioritize remediation based on exposure (network access + IAM scope) | `findings.list` |
| **Misconfiguration findings** | Surface compliance gaps (open ports, public access, key rotation) | `findings.list` |
| **Issues** (grouped findings) | Aggregate related findings for investigation prioritization | `issues.list` |
| **Attack paths** | Step-by-step attack chains for CHOKEPOINT and TOXIC_COMBINATION findings | `attackPaths.list` |
| **Valued resources** | Which specific resources are exposed (the "many valued resources" in CHOKEPOINT findings) | `valuedResources.list` |
| **Simulations** | Attack simulation context and metadata | `simulations.get` |

See also:
- [GCP Onboarding Permissions](gcp-onboarding-permissions.md) — standard IAM investigation roles
- [Google Workspace Integration](gcp-workspace-integration.md) — identity enrichment for user/group investigations
