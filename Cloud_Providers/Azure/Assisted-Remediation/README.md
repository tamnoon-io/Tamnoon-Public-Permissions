# Tamnoon Azure Permissions Overview

This document outlines the Azure permissions required for Tamnoon to investigate,
monitor, and remediate cloud misconfigurations within customer environments.

Tamnoon supports two onboarding methods:

| Method | Description | Identity Type |
|--------|-------------|---------------|
| **Human Onboarding (CloudPro)** | Tamnoon engineer accesses Azure directly | Entra ID User |
| **Platform Onboarding (ARM Template)** | Automated access via federated credentials | App Registration + Service Principal |

Both methods use the **same operational permissions** described in Part A below.

================================================================================
# PART A: OPERATIONAL PERMISSIONS
================================================================================

These permissions are granted to the Tamnoon identity (user or service principal)
for investigation and remediation workflows.

--------------------------------------------------------------------------------
## 1. Azure Built-in Roles (Required)
--------------------------------------------------------------------------------

Assign these roles at the Management Group or Subscription level.

  - **Reader**
    Read-only access to all Azure resource configurations.

    Docs: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/general#reader

  - **Storage Blob Data Reader**
    Read-only access to blob data. Required for reading diagnostic logs stored
    in blob containers (e.g., `insights-logs-auditevent`). Does NOT grant storage
    key access (least-privilege approach).

    Docs: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/storage#storage-blob-data-reader

  - **Log Analytics Reader**
    Read-only access to Azure Monitor Logs and Log Analytics Workspaces.
    Required for audit log access, NSG flow log review, and diagnostics analysis.

    Docs: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/manage-access?tabs=portal#log-analytics-reader

--------------------------------------------------------------------------------
## 2. Microsoft Entra ID Directory Roles (Required)
--------------------------------------------------------------------------------

Required for investigating identity-related misconfigurations (users, groups,
service principals, app registrations).

**Minimum Required:**

  - **Directory Readers**
    Grants read access to users, groups, and applications.

    Docs: https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#directory-readers

**Preferred:**

  - **Global Reader**
    Grants full read-only access to all directory objects including policies.

    Docs: https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#global-reader

--------------------------------------------------------------------------------
## 3. Custom Role (Add-on for Deeper Investigation)
--------------------------------------------------------------------------------

Some workflows require more granular permissions than built-in roles provide.
This custom role enables deeper investigation capabilities and is **optional**
for both onboarding methods.

**Log Analytics (Query & Search)**
- `Microsoft.OperationalInsights/workspaces/analytics/query/action`
- `Microsoft.OperationalInsights/workspaces/search/action`

**Storage Account (Key Access for Diagnostic Logs)**
- `Microsoft.Storage/storageAccounts/listKeys/action`
- `Microsoft.Storage/storageAccounts/listServiceSas/action`

**App Service (Connection Strings & App Settings)**
- `Microsoft.Web/sites/config/list/action`

**Azure Functions (Function & Host Keys)**
- `Microsoft.Web/sites/functions/listkeys/action`
- `Microsoft.Web/sites/host/listkeys/action`

**Key Vault (Data Plane - Secret/Key/Certificate Access)**
- `Microsoft.KeyVault/vaults/secrets/getSecret/action`
- `Microsoft.KeyVault/vaults/secrets/readMetadata/action`
- `Microsoft.KeyVault/vaults/keys/read`
- `Microsoft.KeyVault/vaults/certificates/read`

**Container Registry (Admin Credential Audit)**
- `Microsoft.ContainerRegistry/registries/listCredentials/action`

**Event Hub (Connection String Access for Log Streaming)**
- `Microsoft.EventHub/namespaces/authorizationRules/listKeys/action`

**Cosmos DB (Key & Connection String Access)**
- `Microsoft.DocumentDB/databaseAccounts/listKeys/action`
- `Microsoft.DocumentDB/databaseAccounts/listConnectionStrings/action`

**Assignable Scopes:**
- `/subscriptions/<your-subscription-id>`
- `/providers/Microsoft.Management/managementGroups/<your-mgmt-id>`

This role should be maintained to reflect evolving API capabilities.

--------------------------------------------------------------------------------
## 4. Entra Permissions Management (Optional)
--------------------------------------------------------------------------------

If your environment has Microsoft Entra Permissions Management enabled, Tamnoon
can leverage it for CIEM (Cloud Infrastructure Entitlement Management).

**Required Permission:**
- `microsoft.permissionsManagement/allEntities/allProperties/read`

**Benefits:**
- Detect and reduce excessive permissions
- Auto-remediate least privilege violations
- Strengthen Zero Trust posture

================================================================================
# PART B: ONBOARDING METHODS
================================================================================

--------------------------------------------------------------------------------
## Method 1: Human Onboarding (CloudPro)
--------------------------------------------------------------------------------

A Tamnoon CloudPro engineer is granted direct access to your Azure environment
using their Entra ID user account.

**What You Need to Do:**

1. Invite the Tamnoon user as a Guest in your Entra ID tenant (if external)
2. Assign the Azure RBAC roles from Section 1 (Reader, Storage Blob Data Reader,
   Log Analytics Reader) at the appropriate scope
3. Assign the Entra ID Directory Role from Section 2 (Directory Readers or
   Global Reader)
4. (Optional) Assign the Custom Role from Section 3 for deeper investigation
5. (Optional) Grant Entra Permissions Management access from Section 4

**No ARM template deployment required** - roles are assigned directly to the user.

--------------------------------------------------------------------------------
## Method 2: Platform Onboarding (ARM Template)
--------------------------------------------------------------------------------

The Tamnoon platform accesses your Azure environment using an App Registration
with federated credentials (OIDC trust with AWS Cognito).

**What the Template Creates:**

| Resource | Description |
|----------|-------------|
| App Registration | `TamnoonFederationApp` in Entra ID |
| Service Principal | Enterprise Application for the App Registration |
| Federated Identity Credential | OIDC trust with AWS Cognito (`cognito-identity.amazonaws.com`) |
| Role Assignments | Reader, Log Analytics Reader, Storage Blob Data Reader |

**Template Deployment Scopes:**

| Template | Scope | Role Assignment Inheritance |
|----------|-------|----------------------------|
| Tenant-level | Root Management Group | All subscriptions in tenant |
| Management Group | Target Management Group | All subscriptions under MG |
| Subscription | Single Subscription | That subscription only |

### Deployer Permissions (One-Time Setup)

The identity deploying the ARM template requires:

**Microsoft Entra ID (Minimum):**

  - **Cloud Application Administrator** (Directory Role)
    - Creates App Registration
    - Creates Service Principal
    - Configures Federated Identity Credential

    Docs: https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#cloud-application-administrator

**Azure RBAC (Minimum):**

  - **User Access Administrator** at the deployment scope
    - Assigns roles to the Tamnoon Service Principal

    Docs: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#user-access-administrator

### Conditional Access Considerations

If your organization has Conditional Access policies that block Azure CLI
(error code `53003`: "Access has been blocked by Conditional Access policies"),
use one of these alternatives:

| Alternative | Description |
|-------------|-------------|
| **Azure Cloud Shell** | Usually exempted from CA policies (trusted Azure network) |
| **Azure Portal** | Upload template via Portal → "Deploy a custom template" |
| **Compliant Device** | Run Azure CLI from an Intune-enrolled device |
| **CA Policy Exception** | Temporarily exclude the deploying identity or location |

### Post-Deployment (Optional Add-ons)

After template deployment, you can optionally:
1. Assign the Custom Role (Section 3) to the `TamnoonFederationApp` Service Principal
2. Grant Entra Permissions Management access (Section 4)

================================================================================
# SUMMARY
================================================================================

--------------------------------------------------------------------------------
## Permissions Matrix
--------------------------------------------------------------------------------

| Permission Type | Human (CloudPro) | Platform (ARM Template) |
|-----------------|------------------|------------------------|
| Reader | Assign to User | Auto-assigned by Template |
| Storage Blob Data Reader | Assign to User | Auto-assigned by Template |
| Log Analytics Reader | Assign to User | Auto-assigned by Template |
| Directory Readers / Global Reader | Assign to User | Assign to Service Principal |
| Custom Role (Add-on) | Assign to User | Assign to Service Principal |
| Entra Permissions Mgmt (Optional) | Assign to User | Assign to Service Principal |

--------------------------------------------------------------------------------
## Deployer Permissions (Platform Onboarding Only)
--------------------------------------------------------------------------------

| Domain | Role | Purpose |
|--------|------|---------|
| Entra ID | Cloud Application Administrator | Create App, SPN, Federated Credentials |
| Azure RBAC | User Access Administrator | Assign roles at deployment scope |

--------------------------------------------------------------------------------
## Implementation Notes
--------------------------------------------------------------------------------

- Assign roles at the narrowest applicable scope
- Maintain audit trails using Azure Activity Logs
- Keep custom role definitions up to date
- Review role assignments periodically

--------------------------------------------------------------------------------
## Support and Contact
--------------------------------------------------------------------------------

For help configuring access or assigning roles, please contact your Tamnoon
CloudPros integration engineer.

Maintained by: https://tamnoon.io
Last Updated: January 12th, 2026
