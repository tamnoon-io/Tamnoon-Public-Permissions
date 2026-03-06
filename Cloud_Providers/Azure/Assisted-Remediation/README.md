# Tamnoon Azure Permissions Overview

This document outlines the Azure permissions required for Tamnoon to investigate,
monitor, and remediate cloud misconfigurations within customer environments.

Tamnoon supports two onboarding methods:

| Method | Description | Identity Type |
|--------|-------------|---------------|
| **Platform Onboarding (Bicep Template)** | Automated access via federated credentials | App Registration + Service Principal |
| **Human Onboarding (CloudPro)** | Tamnoon engineer accesses Azure directly | Entra ID User |

Both methods use the **same operational permissions** described in Part A below.

---

# Part A: Operational Permissions

These permissions are granted to the Tamnoon identity (user or service principal)
for investigation and remediation workflows.

## Required Roles

| # | Role | Type | Scope | Purpose |
|---|------|------|-------|---------|
| 1 | [Reader](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/general#reader) | Azure RBAC | Mgmt Group / Subscription | Read-only access to all resource configurations |
| 2 | [Storage Blob Data Reader](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/storage#storage-blob-data-reader) | Azure RBAC | Mgmt Group / Subscription | Read diagnostic logs in blob containers |
| 3 | [Log Analytics Reader](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/manage-access?tabs=portal#log-analytics-reader) | Azure RBAC | Mgmt Group / Subscription | Query Azure Monitor Logs and Log Analytics Workspaces |
| 4 | [**Directory Readers**](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#directory-readers) | **Entra ID** | Tenant | Resolve principal GUIDs to display names |

> **Why Directory Readers?** Without this role, callers in data plane logs appear as opaque GUIDs — identity context is missing from all findings. This role grants read access to users, groups, service principals, and applications in Microsoft Entra ID, enabling Tamnoon to map every principal UUID to a human-readable name during access pattern analysis (Storage, Key Vault, SQL Server, etc.).

## Custom Role — Deeper Investigation

Some investigation workflows require more granular permissions than the built-in roles provide.
This custom role enables deeper capabilities and is **optional** for both onboarding methods.

| Permission | Service | Investigation Use Case |
|-----------|---------|----------------------|
| `Microsoft.OperationalInsights/workspaces/analytics/query/action` | Log Analytics | KQL queries for access pattern analysis and security event correlation |
| `Microsoft.OperationalInsights/workspaces/search/action` | Log Analytics | Search within Log Analytics workspace data |
| `Microsoft.Storage/storageAccounts/listKeys/action` | Storage | Container, file share, queue, and table security analysis |
| `Microsoft.Storage/storageAccounts/listServiceSas/action` | Storage | SAS token policy and delegation audit |
| `Microsoft.Web/sites/config/list/action` | App Service | Connection strings and app settings exposure analysis |
| `Microsoft.Web/sites/functions/listkeys/action` | Azure Functions | Function-level key access for secrets exposure audit |
| `Microsoft.Web/sites/host/listkeys/action` | Azure Functions | Host-level key access for secrets exposure audit |
| `Microsoft.KeyVault/vaults/secrets/getSecret/action` | Key Vault | Secret value retrieval for rotation and exposure validation |
| `Microsoft.KeyVault/vaults/secrets/readMetadata/action` | Key Vault | Secret metadata (expiry, enabled state) without value access |
| `Microsoft.KeyVault/vaults/keys/read` | Key Vault | Key metadata for cryptographic posture review |
| `Microsoft.KeyVault/vaults/certificates/read` | Key Vault | Certificate metadata for expiry and binding review |
| `Microsoft.ContainerRegistry/registries/listCredentials/action` | Container Registry | Admin credential audit for registry access posture |
| `Microsoft.EventHub/namespaces/authorizationRules/listKeys/action` | Event Hub | Connection string access for log streaming analysis |
| `Microsoft.DocumentDB/databaseAccounts/listKeys/action` | Cosmos DB | Account key access for data plane security review |
| `Microsoft.DocumentDB/databaseAccounts/listConnectionStrings/action` | Cosmos DB | Connection string audit for secrets exposure |

### Assignable Scopes

- `/subscriptions/<subscription-id>`
- `/providers/Microsoft.Management/managementGroups/<management-group-id>`

### Role Definition — Subscription Scope

```jsonc
{
  "Name": "Tamnoon Custom Role",
  "IsCustom": true,
  "Description": "Tamnoon Custom Role Permissions (subscription scope).",
  "Actions": [
    "Microsoft.OperationalInsights/workspaces/analytics/query/action",
    "Microsoft.OperationalInsights/workspaces/search/action",
    "Microsoft.Storage/storageAccounts/listKeys/action",
    "Microsoft.Storage/storageAccounts/listServiceSas/action",
    "Microsoft.Web/sites/config/list/action",
    "Microsoft.Web/sites/functions/listkeys/action",
    "Microsoft.Web/sites/host/listkeys/action",
    "Microsoft.KeyVault/vaults/secrets/getSecret/action",
    "Microsoft.KeyVault/vaults/secrets/readMetadata/action",
    "Microsoft.KeyVault/vaults/keys/read",
    "Microsoft.KeyVault/vaults/certificates/read",
    "Microsoft.ContainerRegistry/registries/listCredentials/action",
    "Microsoft.EventHub/namespaces/authorizationRules/listKeys/action",
    "Microsoft.DocumentDB/databaseAccounts/listKeys/action",
    "Microsoft.DocumentDB/databaseAccounts/listConnectionStrings/action"
  ],
  "NotActions": [],
  "DataActions": [],
  "NotDataActions": [],
  "AssignableScopes": [
    "/subscriptions/<subscription-id>"
  ]
}
```

### Role Definition — Management Group Scope

```jsonc
{
  "Name": "Tamnoon Custom Role",
  "IsCustom": true,
  "Description": "Tamnoon Custom Role Permissions (management-group scope).",
  "Actions": [
    "Microsoft.OperationalInsights/workspaces/analytics/query/action",
    "Microsoft.OperationalInsights/workspaces/search/action",
    "Microsoft.Storage/storageAccounts/listKeys/action",
    "Microsoft.Storage/storageAccounts/listServiceSas/action",
    "Microsoft.Web/sites/config/list/action",
    "Microsoft.Web/sites/functions/listkeys/action",
    "Microsoft.Web/sites/host/listkeys/action",
    "Microsoft.KeyVault/vaults/secrets/getSecret/action",
    "Microsoft.KeyVault/vaults/secrets/readMetadata/action",
    "Microsoft.KeyVault/vaults/keys/read",
    "Microsoft.KeyVault/vaults/certificates/read",
    "Microsoft.ContainerRegistry/registries/listCredentials/action",
    "Microsoft.EventHub/namespaces/authorizationRules/listKeys/action",
    "Microsoft.DocumentDB/databaseAccounts/listKeys/action",
    "Microsoft.DocumentDB/databaseAccounts/listConnectionStrings/action"
  ],
  "NotActions": [],
  "DataActions": [],
  "NotDataActions": [],
  "AssignableScopes": [
    "/providers/Microsoft.Management/managementGroups/<management-group-id>"
  ]
}
```

This role should be maintained to reflect evolving API capabilities.
See [azure-custom-role.md](azure-custom-role.md) for detailed permission specifications.

---

# Part B: Onboarding Methods

## Method 1: Platform Onboarding (Bicep Template)

The Tamnoon platform accesses your Azure environment using an App Registration
with federated credentials (OIDC trust with AWS Cognito). This is the
**recommended onboarding method**.

### What the Template Creates

| Resource | Description |
|----------|-------------|
| App Registration | `TamnoonFederationApp` in Entra ID |
| Service Principal | Enterprise Application for the App Registration |
| Federated Identity Credential | OIDC trust with AWS Cognito (`cognito-identity.amazonaws.com`) |
| Role Assignments (RBAC) | Reader, Log Analytics Reader, Storage Blob Data Reader |
| Role Assignment (Entra ID) | Directory Readers |

### Template Outputs

| Output | Description |
|--------|-------------|
| `tenantId` | Your Entra ID tenant ID |
| `applicationId` | The App Registration (client) ID |
| `servicePrincipalObjectId` | The Service Principal object ID — needed if assigning the Custom Role post-deployment |

### Deployment Scopes

The same Bicep template is available at each scope level — select the one that
matches your desired role assignment inheritance:

| Template Scope | Role Assignment Inheritance |
|----------------|----------------------------|
| Tenant (Root Management Group) | All subscriptions in tenant |
| Management Group | All subscriptions under that MG |
| Subscription | That subscription only |

### Deployer Permissions (One-Time Setup)

The identity deploying the Bicep template requires:

**Entra ID:**

| Role | Purpose |
|------|---------|
| [Cloud Application Administrator](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#cloud-application-administrator) | Create App Registration, Service Principal, and Federated Identity Credential |
| [Privileged Role Administrator](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#privileged-role-administrator) (or Global Administrator) | Assign Directory Readers role to the Service Principal |

**Azure RBAC:**

| Role | Purpose |
|------|---------|
| [User Access Administrator](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#user-access-administrator) at deployment scope | Assign Azure RBAC roles to the Tamnoon Service Principal |

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

### Post-Deployment (Optional Add-on)

After template deployment, you can optionally assign the Custom Role
to the `TamnoonFederationApp` Service Principal for deeper investigation capabilities.
Use the `servicePrincipalObjectId` from the template outputs to target the assignment.

## Method 2: Human Onboarding (CloudPro)

A Tamnoon CloudPro engineer is granted direct access to your Azure environment
using their Entra ID user account.

**What you need to do:**

1. Invite the Tamnoon user as a Guest in your Entra ID tenant (if external)
2. Assign the three Azure RBAC roles (Reader, Storage Blob Data Reader, Log Analytics Reader) at the appropriate scope
3. Assign the Entra ID role — [Directory Readers](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#directory-readers)
4. *(Optional)* Assign the Custom Role for deeper investigation

No template deployment required — roles are assigned directly to the user.

---

# Summary

## Permissions Matrix

| Permission | Platform (Bicep Template) | Human (CloudPro) |
|------------|--------------------------|-------------------|
| Reader | Auto-assigned by Template | Assign to User |
| Storage Blob Data Reader | Auto-assigned by Template | Assign to User |
| Log Analytics Reader | Auto-assigned by Template | Assign to User |
| Directory Readers | Auto-assigned by Template | Assign to User |
| Custom Role (Add-on) | Assign to Service Principal | Assign to User |

## Deployer Permissions (Platform Onboarding Only)

| Domain | Role | Purpose |
|--------|------|---------|
| Entra ID | Cloud Application Administrator | Create App, SPN, Federated Credentials |
| Entra ID | Privileged Role Administrator | Assign Directory Readers to SPN |
| Azure RBAC | User Access Administrator | Assign Azure RBAC roles at deployment scope |

## Implementation Notes

- Assign roles at the narrowest applicable scope
- Maintain audit trails using Azure Activity Logs
- Keep custom role definitions up to date — see [azure-custom-role.md](azure-custom-role.md)
- Review role assignments periodically

## Support

For help configuring access or assigning roles, contact your Tamnoon
CloudPros integration engineer.

Maintained by: [tamnoon.io](https://tamnoon.io)
