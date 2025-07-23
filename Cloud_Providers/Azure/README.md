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

  - **Reader and Data Access**
    Description: Same as Reader, but includes read access to storage data (blobs, files).

    Docs: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/storage#reader-and-data-access

  - **Log Analytics Reader**
    Description: Read-only access to Azure Monitor Logs and Log Analytics Workspaces.
    Use Case: For audit log access, NSG flow log review, diagnostics.

    Docs: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/manage-access?tabs=portal#log-analytics-reader

--------------------------------------------------------------------------------
# 2. Tamnoon Azure Custom Role
--------------------------------------------------------------------------------

Some workflows require more granular permissions than those available in 
built-in roles. Tamnoon defines a custom role with only the actions necessary 
for deeper investigation and secure remediation tasks.Custom Role is designed 
to evolve over time

Actions Granted:

  - `Microsoft.Web/sites/functions/read`
  - `Microsoft.Web/sites/config/list/action`
  - `Microsoft.Storage/storageAccounts/listKeys/action`

Assignable Scopes:
  - /subscriptions/<subscription-id>

  OR

  - /providers/Microsoft.Management/managementGroups/<mg-id>

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
# 5. Summary Matrix
--------------------------------------------------------------------------------

| Component                       | Required Roles / Permissions                          |
|--------------------------------|--------------------------------------------------------|
| Azure Resource Visibility      | Reader, Reader and Data Access, Log Analytics Reader  |
| Targeted Investigation         | Tamnoon Custom Role                                   |
| Identity & IAM Insights        | Global Reader (preferred) or Directory Readers        |
| CIEM (Optional)                | Global Reader or custom role for Permissions Mgmt     |

--------------------------------------------------------------------------------
# 6. Implementation Notes
--------------------------------------------------------------------------------

- Assign roles using Azure Portal, Azure CLI, PowerShell, or ARM templates.
- Scope roles to the narrowest applicable level.
- Maintain audit trails using Azure Activity Logs.
- Keep custom role definitions up to date.

--------------------------------------------------------------------------------
# 7. Support and Contact
--------------------------------------------------------------------------------

For help configuring access or assigning roles, please contact your Tamnoon 
CloudPros integration engineer. 

Maintained by: https://tamnoon.io  
Last Updated: July 23rd, 2025