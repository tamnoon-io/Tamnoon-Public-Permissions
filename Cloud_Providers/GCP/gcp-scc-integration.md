<img src="images/Tamnoon.png" width="470">

# GCP Security Command Center Integration

Enables Tamnoon to ingest SCC findings (assets, threats, vulnerabilities, attack paths) for correlation with IAM investigation data. This is an **optional** integration — it requires dedicated SCC roles in addition to the [standard onboarding roles](gcp-onboarding-permissions.md).

---

## 1. Prerequisites

### SCC Activation Level

SCC can be activated at organization level or on specific folders. The roles required depend on the activation scope.

| SCC Activation | Tamnoon Roles Granted At | Coverage |
|----------------|--------------------------|----------|
| **Organization-wide** | Organization | All findings across the org |
| **Specific folders** | Each folder with SCC active | Findings within those folders only |

### Standard Onboarding

The [GCP onboarding roles](gcp-onboarding-permissions.md) (`roles/viewer`, `roles/browser`, `roles/iam.securityReviewer`, etc.) must be assigned first. SCC roles are **in addition to** the standard roles — they do not replace them.

**Note**: Neither `roles/viewer` nor `roles/iam.securityReviewer` include SCC permissions. SCC has its own dedicated role family (`roles/securitycenter.*`).

---

## 2. Organization-Level SCC

When SCC is activated at the organization level, a single role provides full read access:

| Role | Permissions | Scope |
|------|-------------|-------|
| `roles/securitycenter.adminViewer` | Read-only access to ALL assets, findings, attack paths, and security sources | Organization-wide |

This is the recommended approach — it covers all SCC data across the entire organization.

---

## 3. Folder-Level SCC

When SCC is activated on specific folders (not org-wide), granular roles are required on each folder:

| Role | Purpose |
|------|---------|
| `roles/securitycenter.assetsViewer` | Read access to SCC assets |
| `roles/securitycenter.findingsViewer` | Read access to SCC findings (threats, vulnerabilities, misconfigurations) |
| `roles/securitycenter.attackPathsViewer` | Read access to SCC attack path simulations |

All three roles must be granted on **each folder** where SCC is active.

**Note**: `roles/securitycenter.attackPathsViewer` cannot be granted at project level — folder or organization scope is required.

---

## 4. What Tamnoon Ingests

| SCC Data Type | Usage |
|---------------|-------|
| **Threat findings** (active) | Correlate with IAM bindings — which identities have access to affected resources |
| **Vulnerability findings** | Prioritize remediation based on exposure (network access + IAM scope) |
| **Asset inventory** | Cross-reference with IAM analysis for comprehensive resource coverage |
| **Attack paths** | Understand lateral movement risk through IAM role chains |

**Integration with IAM investigations**: SCC findings provide the "what is at risk" context, while the standard onboarding roles provide the "who has access" context. Together they answer: "this resource has a vulnerability, and these identities can reach it."

---

## 5. Summary

| SCC Scope | Roles | Granted At |
|-----------|-------|------------|
| **Organization** | `roles/securitycenter.adminViewer` | Organization |
| **Folder** | `roles/securitycenter.assetsViewer`, `roles/securitycenter.findingsViewer`, `roles/securitycenter.attackPathsViewer` | Each SCC-active folder |
| **Project** | Not supported for attack paths | — |

See also:
- [GCP Onboarding Permissions](gcp-onboarding-permissions.md) — standard IAM investigation roles (required)
- [Google Workspace Integration](gcp-workspace-integration.md) — identity enrichment for user/group investigations (optional)
