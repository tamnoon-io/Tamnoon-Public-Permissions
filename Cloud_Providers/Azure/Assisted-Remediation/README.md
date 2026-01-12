# Tamnoon CloudPros – Azure Permissions Overview

This document outlines the Azure permissions required for Tamnoon CloudPros to
investigate, monitor, and remediate cloud misconfigurations within customer
environments. It includes a blend of Azure Built-in Roles, a Custom Role, and 
Microsoft Entra ID (formerly Azure Active Directory) Directory Roles.

All permissions are scoped to follow the principle of least privilege, and are 
intended to grant Tamnoon read-level visibility and scoped remediation rights 
without broad write or administrative access.

--------------------------------------------------------------------------------
# 1. Azure Built-in Roles
--------------------------------------------------------------------------------

These are the standard Azure RBAC roles required by Tamnoon-managed users or 
service principals for visibility and investigation workflows. They are usually 
assigned at the management group or subscription level.

# Required Roles:

  - **Reader**
    Description: Read-only access to all resource types.

    Docs: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/general#reader

  - **Storage Blob Data Reader**
    Description: Read-only access to blob data. Sufficient for reading diagnostic logs
    stored in blob containers (e.g., `insights-logs-auditevent`). Does NOT grant
    storage key access (least-privilege approach).

    Docs: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/storage#storage-blob-data-reader

  - **Log Analytics Reader**
    Description: Read-only access to Azure Monitor Logs and Log Analytics Workspaces.
    Use Case: For audit log access, NSG flow log review, diagnostics.

    Docs: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/manage-access?tabs=portal#log-analytics-reader

--------------------------------------------------------------------------------
# 2. Tamnoon Azure Custom Role
--------------------------------------------------------------------------------

Some workflows require more granular permissions than those available in
built-in roles. Tamnoon defines a custom role with only the actions necessary
for deeper investigation and secure remediation tasks. Custom Role is designed
to evolve over time.

Actions Granted:

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

Assignable Scopes:
  - /subscriptions/<your-subscription-id>

  OR

  - /providers/Microsoft.Management/managementGroups/<your-mgmt-id>

This role should be maintained to reflect evolving API capabilities and Tamnoon
service expansion.


--------------------------------------------------------------------------------
# 3. Microsoft Entra ID (Directory Roles)
--------------------------------------------------------------------------------

To investigate identity-related misconfigurations (users, groups, service 
principals, app registrations), Tamnoon requires access to Microsoft Entra ID 
resources.

**Minimum Required Role:**

  - **Directory Readers**
    Grants read access to users, groups, and applications.

    Docs: https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#directory-readers

**Preferred Role:**

  - **Global Reader**
    Grants full read-only access to all directory objects including policies.

    Docs: https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#global-reader

--------------------------------------------------------------------------------
# 4. Entra Permissions Management (Optional)
--------------------------------------------------------------------------------

If your environment has Microsoft Entra Permissions Management enabled, Tamnoon 
can leverage it for CIEM (Cloud Infrastructure Entitlement Management) to detect 
unused or excessive permissions.

**Required Permission:**
  - `microsoft.permissionsManagement/allEntities/allProperties/read`

Benefits:
  - Detect and reduce excessive permissions
  - Auto-remediate least privilege violations
  - Strengthen Zero Trust posture

--------------------------------------------------------------------------------
# 5. Onboarding Deployment Permissions
--------------------------------------------------------------------------------

The following permissions are required by the identity (user or service principal)
that deploys the Tamnoon onboarding template via Azure CLI or Portal.

## Microsoft Entra ID (Minimum)

  - **Cloud Application Administrator** (Directory Role)
    Required to:
    - Create App Registration (`TamnoonFederationApp`)
    - Create Service Principal (Enterprise Application)
    - Configure Federated Identity Credential (AWS Cognito OIDC trust)

    Docs: https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#cloud-application-administrator

## Azure RBAC (Minimum)

  - **User Access Administrator** at the deployment scope
    Required to assign roles (Reader, Log Analytics Reader, Storage Blob Data Reader)
    to the Tamnoon Service Principal.

    | Template Scope     | User Access Administrator Scope        |
    |--------------------|----------------------------------------|
    | Tenant-level       | Root Management Group                  |
    | Management Group   | Target Management Group                |
    | Subscription       | Target Subscription                    |

    Docs: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#user-access-administrator

## Conditional Access Considerations

If your organization has Conditional Access policies that block Azure CLI
(error code `53003`: "Access has been blocked by Conditional Access policies"),
use one of these alternatives:

| Alternative              | Description                                              |
|--------------------------|----------------------------------------------------------|
| **Azure Cloud Shell**    | Usually exempted from CA policies (trusted Azure network)|
| **Azure Portal**         | Upload template via Portal → "Deploy a custom template"  |
| **Compliant Device**     | Run Azure CLI from an Intune-enrolled device             |
| **CA Policy Exception**  | Temporarily exclude the deploying identity or location   |

--------------------------------------------------------------------------------
# 6. Summary Matrix
--------------------------------------------------------------------------------

| Component                       | Required Roles / Permissions                              |
|--------------------------------|-----------------------------------------------------------|
| Azure Resource Visibility      | Reader, Storage Blob Data Reader, Log Analytics Reader    |
| Targeted Investigation         | Tamnoon Custom Role                                       |
| Identity & IAM Insights        | Global Reader (preferred) or Directory Readers            |
| CIEM (Optional)                | Global Reader or custom role for Permissions Mgmt         |
| Onboarding Deployment          | Cloud Application Administrator + User Access Administrator |

--------------------------------------------------------------------------------
# 7. Implementation Notes
--------------------------------------------------------------------------------

- Assign roles using Azure Portal, Azure CLI, PowerShell, or ARM templates.
- Scope roles to the narrowest applicable level.
- Maintain audit trails using Azure Activity Logs.
- Keep custom role definitions up to date.

--------------------------------------------------------------------------------
# 8. Support and Contact
--------------------------------------------------------------------------------

For help configuring access or assigning roles, please contact your Tamnoon
CloudPros integration engineer.

Maintained by: https://tamnoon.io
Last Updated: January 12th, 2026