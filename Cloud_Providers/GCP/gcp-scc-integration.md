<img src="images/Tamnoon.png" width="470">

# GCP Security Command Center Integration

## Standard Path — No Separate SCC Roles Needed

`roles/iam.securityReviewer` (assigned during [standard onboarding](gcp-onboarding-permissions.md)) includes 22 SCC permissions:

| Permission | Capability |
|------------|------------|
| `securitycenter.findings.list` | List threat, vulnerability, and misconfiguration findings |
| `securitycenter.assets.list` | List SCC asset inventory |
| `securitycenter.attackpaths.list` | List attack path simulations |
| `securitycenter.sources.list` | List SCC finding sources |
| `securitycenter.muteconfigs.list` | List mute configurations |
| `securitycenter.notificationconfig.list` | List notification configs |
| + 16 additional list/read permissions | Compliance snapshots, risk reports, custom modules, valued resources |

**No additional configuration is required** when Tamnoon is onboarded at organization or folder level with `roles/iam.securityReviewer`.

---

## Fallback — Dedicated SCC Roles

Dedicated SCC roles are only needed when:
- The customer wants **granular SCC role control** separate from the security reviewer role
- SCC is activated at folder level and the customer prefers dedicated SCC roles per folder
- `roles/iam.securityReviewer` cannot be assigned for policy reasons

### Organization-Level SCC

| Role | Permissions | Scope |
|------|-------------|-------|
| `roles/securitycenter.adminViewer` | Read-only access to ALL assets, findings, attack paths, and security sources | Organization-wide |

### Folder-Level SCC

| Role | Purpose |
|------|---------|
| `roles/securitycenter.assetsViewer` | Read access to SCC assets |
| `roles/securitycenter.findingsViewer` | Read access to SCC findings |
| `roles/securitycenter.attackPathsViewer` | Read access to SCC attack path simulations |

All three roles must be granted on **each folder** where SCC is active.

**Note**: `roles/securitycenter.attackPathsViewer` cannot be granted at project level.

---

## What Tamnoon Ingests

| SCC Data Type | Usage |
|---------------|-------|
| **Threat findings** (active) | Correlate with IAM bindings — which identities have access to affected resources |
| **Vulnerability findings** | Prioritize remediation based on exposure (network access + IAM scope) |
| **Asset inventory** | Cross-reference with IAM analysis for comprehensive resource coverage |
| **Attack paths** | Understand lateral movement risk through IAM role chains |

See also:
- [GCP Onboarding Permissions](gcp-onboarding-permissions.md) — standard IAM investigation roles
- [Google Workspace Integration](gcp-workspace-integration.md) — identity enrichment for user/group investigations
