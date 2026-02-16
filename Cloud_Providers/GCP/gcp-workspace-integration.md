<img src="images/Tamnoon.png" width="470">

# Google Workspace Integration

Enriches GCP IAM investigations with identity context from Google Workspace / Cloud Identity. This is an **optional** integration — GCP IAM investigations work without it, but Workspace data fills critical gaps when investigating user and group principals.

---

## 1. What It Provides

| Investigation Gap (GCP IAM only) | With Workspace Integration |
|----------------------------------|---------------------------|
| User principal is just an email address | Full name, department, organizational unit, employment status |
| No way to detect stale users | `lastLoginTime`, `suspended`, `archived` fields — definitive answer |
| Group bindings show group email only | Expand group → list all members (blast radius of the IAM binding) |
| Nested groups invisible | Recursive group membership resolution |
| No org structure context | OU hierarchy reveals business unit, region, contractor vs employee |
| SA ownership unknown | Complement with SA `description` field parsing (see Section 5) |

---

## 2. Prerequisites

### Workspace Admin Actions

The customer's **Google Workspace Super Admin** (or delegated admin with API management privileges) must perform the following steps.

### Step 1: Enable Admin SDK API

1. Go to **Google Cloud Console** > **APIs & Services** > **Library**
2. Select the GCP project associated with Workspace (or any project in the org)
3. Search for **Admin SDK API** and click **Enable**

API service name: `admin.googleapis.com`

### Step 2: Register Tamnoon SA for Domain-Wide Delegation

Domain-wide delegation allows the Tamnoon service account to call Workspace Admin SDK APIs by impersonating a designated admin user. No Workspace admin role assignment is needed — the delegation grant itself defines the access.

1. Go to **Google Workspace Admin Console** (`admin.google.com`)
2. Navigate to **Security** > **Access and data control** > **API controls**
3. Click **Manage Domain Wide Delegation**
4. Click **Add new**
5. Enter the following:

| Field | Value |
|-------|-------|
| **Client ID** | Tamnoon service account's OAuth2 Client ID (numeric, provided during onboarding) |
| **OAuth scopes** | See Section 3 below (comma-separated) |

6. Click **Authorize**

### Step 3: Designate an Impersonation Target User

The Tamnoon SA impersonates a Workspace user when calling Admin SDK. This user must have sufficient admin privileges to read the requested data.

**Recommended**: Create a dedicated service user (e.g., `tamnoon-reader@customer-domain.com`) with a **custom admin role** that has read-only access:

| Admin Console Privilege | Category |
|------------------------|----------|
| Users > Read | Organization Units |
| Groups > Read | Groups |
| Organizational Units > Read | Organization Units |

This follows least-privilege — the impersonated user only has read access, matching the OAuth scopes.

**Alternative**: Use an existing Super Admin account as the impersonation target. Simpler but grants broader access than needed.

---

## 3. Required OAuth Scopes

All scopes are **read-only**. No write or management access is requested.

| OAuth Scope | Purpose |
|-------------|---------|
| `https://www.googleapis.com/auth/admin.directory.user.readonly` | List and read user profiles (name, OU, status, last login) |
| `https://www.googleapis.com/auth/admin.directory.group.readonly` | List groups and group memberships |
| `https://www.googleapis.com/auth/admin.directory.orgunit.readonly` | Read organizational unit hierarchy |

**Comma-separated (for Admin Console paste):**
```
https://www.googleapis.com/auth/admin.directory.user.readonly,https://www.googleapis.com/auth/admin.directory.group.readonly,https://www.googleapis.com/auth/admin.directory.orgunit.readonly
```

---

## 4. How It Complements IAM Investigations

### User Principal Investigations

When an IAM binding contains `user:alice@company.com`, Workspace resolves:

```
User:                   alice@company.com
  Display Name:         Alice Johnson
  Org Unit:             /Engineering/Platform
  Status:               Active
  Last Login:           2026-02-10
  Created:              2023-06-15
```

**Investigation value**: Suspended or archived users with active IAM bindings are stale access — immediate remediation candidates. OU context helps triage (contractor OU vs employee OU has different risk profiles).

### Group Principal Investigations

When an IAM binding contains `group:platform-admins@company.com` with `roles/editor`, Workspace expands:

```
Group:                  platform-admins@company.com
  Members:              12 users, 2 nested groups
  Effective Members:    47 (after nested group expansion)
  Blast Radius:         47 identities inherit roles/editor
```

**Investigation value**: A single group binding can grant high-privilege roles to dozens of users. Without Workspace, this blast radius is invisible — GCP IAM only shows the group email.

### Stale Identity Detection

| Signal | Source | Meaning |
|--------|--------|---------|
| `lastLoginTime` > 90 days | Workspace Admin SDK | User hasn't signed in — likely departed or role-changed |
| `suspended: true` | Workspace Admin SDK | User explicitly disabled — IAM bindings should be removed |
| `archived: true` | Workspace Admin SDK | User archived — still consumes license, no access |
| SA `description` contains `owners` | GCP IAM API | SA owner may have departed — cross-reference with Workspace |

### Script Integration Points

| Script | Workspace Enrichment | Benefit |
|--------|---------------------|---------|
| `service_account_usage.py` | Resolve group bindings → member count, expand nested groups | Blast radius of group-based SA access |
| `service_account_usage.py` | Parse SA `description` → cross-reference owners with Workspace status | Flag SAs owned by departed users |
| `gcpvm_analysis.py` | Resolve `user:` / `group:` in IAM policies | Identity context for VM access investigation |
| `gcpserverless_analysis.py` | Resolve invoker bindings (`allUsers` vs specific groups) | Understand who can invoke the service |
| `serviceaccountkeyusage.py` | Parse SA `description` → owner status in Workspace | Flag keys for SAs owned by departed users |

---

## 5. Service Account Ownership via Description Field

GCP service accounts have a freeform `description` field that teams often use to store structured ownership metadata:

```json
{
  "owners": ["alice@company.com", "bob@company.com"],
  "provenance": "terraform",
  "tickets": ["CAE-23848"]
}
```

| Field | Meaning |
|-------|---------|
| `owners` | Human contacts responsible for this SA |
| `provenance` | How the SA was created (terraform, gcloud, console) |
| `tickets` | Change management traceability (Jira, ServiceNow, etc.) |

**With Workspace integration**: Cross-reference `owners` emails with Workspace user status. An SA owned by a suspended/departed user with no other active owners is an orphaned SA — high priority for review.

**Without Workspace integration**: The `description` field still provides valuable context (ownership, provenance, ticket references) even without the ability to validate owner status.

**Parsing strategy**: Attempt JSON parse of the `description` field. If it fails, treat as plain text (some SAs use human-readable descriptions like "App Engine default service account"). Both formats are displayed in investigation output.

---

## 6. Authentication Flow

```
Tamnoon SA                    Google Workspace
    |                              |
    |-- SignJwt (sub=admin@co) --> |
    |   aud=oauth2.googleapis.com  |
    |   scope=admin.directory.*    |
    |                              |
    |<-- Access Token ------------ |
    |                              |
    |-- Admin SDK API call ------> |
    |   (Users, Groups, OUs)       |
    |                              |
    |<-- Identity Data ----------- |
```

The SA uses its GCP credentials to sign a JWT with `sub` set to the designated impersonation target user. Google validates the domain-wide delegation grant and returns an access token scoped to the authorized OAuth scopes. The SA then calls Admin SDK APIs using this token.

**Audit trail**: All Admin SDK calls appear in the Workspace Admin audit log under the impersonated user's identity, with the SA email visible in the delegated caller metadata.

---

## 7. Summary

| Component | Requirement | Owner |
|-----------|-------------|-------|
| Admin SDK API enabled | `admin.googleapis.com` on a GCP project in the org | Workspace Admin |
| Domain-wide delegation | SA Client ID + OAuth scopes registered in Admin Console | Workspace Admin |
| Impersonation target user | Workspace user with read-only admin role | Workspace Admin |
| Tamnoon SA Client ID | Provided during onboarding | Tamnoon |
| SA `description` parsing | No additional permissions — uses existing `iam.googleapis.com` access | Already covered by `roles/viewer` |

**Scope**: Workspace integration is **organization-wide** — once configured, it covers all users and groups in the Workspace domain. There is no per-project or per-folder scoping for Workspace data.
