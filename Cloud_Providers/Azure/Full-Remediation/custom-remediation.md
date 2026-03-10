# Tamnoon Azure Full-Remediation Permissions

This document outlines the additional permissions required to enable Tamnoon remediation
workflows — NSG rule management, secret rotation guidance, storage hardening, App Service
access restrictions, and Entra ID hygiene.

> **Prerequisite:** Complete [Assisted-Remediation](../Assisted-Remediation/README.md) onboarding first. That deploys the Bicep template which creates the `TamnoonFederationApp` Service Principal with investigation-level permissions (Reader, Storage Blob Data Reader, Log Analytics Reader, Directory Readers). Full-Remediation builds on top of that foundation.

---

## Azure Resource Remediation

Choose one of the following options to grant remediation permissions to the
`TamnoonFederationApp` Service Principal.

### Option 1: Built-in Roles

Deploy built-in roles at Management Group or Subscription scope:

| Configuration | Roles | Trade-off |
|---------------|-------|-----------|
| **Broad coverage** | [Contributor](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#contributor) + [User Access Administrator](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#user-access-administrator) | Fast setup, no maintenance — grants more permissions than currently used |
| **Maximum coverage** | [Owner](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#owner) | Single role, full control — broadest blast radius |

**When to use Option 1:**
- Rapid onboarding where time-to-value matters more than permission granularity
- Environments where Tamnoon is trusted with broad write access
- No organizational requirement for custom role definitions

### Option 2: Custom Role (Recommended)

A purpose-built role containing only the permissions Tamnoon remediation workflows
actually require. This role **includes** the investigation permissions from
[Assisted-Remediation](../Assisted-Remediation/README.md) so a single custom role
covers both investigation and remediation.

#### Investigation Permissions (15)

These are the same as the Assisted-Remediation custom role — included here so
a single role assignment covers both workflows.

| Permission | Service | Use Case |
|-----------|---------|----------|
| `Microsoft.OperationalInsights/workspaces/analytics/query/action` | Log Analytics | KQL queries for access pattern analysis |
| `Microsoft.OperationalInsights/workspaces/search/action` | Log Analytics | Workspace data search |
| `Microsoft.Storage/storageAccounts/listKeys/action` | Storage | Container, share, queue, table analysis |
| `Microsoft.Storage/storageAccounts/listServiceSas/action` | Storage | SAS token policy audit |
| `Microsoft.Web/sites/config/list/action` | App Service | Connection strings and app settings |
| `Microsoft.Web/sites/functions/listkeys/action` | Azure Functions | Function-level key audit |
| `Microsoft.Web/sites/host/listkeys/action` | Azure Functions | Host-level key audit |
| `Microsoft.KeyVault/vaults/secrets/getSecret/action` | Key Vault | Secret rotation validation |
| `Microsoft.KeyVault/vaults/secrets/readMetadata/action` | Key Vault | Secret expiry and state |
| `Microsoft.KeyVault/vaults/keys/read` | Key Vault | Cryptographic posture review |
| `Microsoft.KeyVault/vaults/certificates/read` | Key Vault | Certificate expiry and binding |
| `Microsoft.ContainerRegistry/registries/listCredentials/action` | Container Registry | Admin credential audit |
| `Microsoft.EventHub/namespaces/authorizationRules/listKeys/action` | Event Hub | Log streaming analysis |
| `Microsoft.DocumentDB/databaseAccounts/listKeys/action` | Cosmos DB | Data plane security review |
| `Microsoft.DocumentDB/databaseAccounts/listConnectionStrings/action` | Cosmos DB | Connection string audit |

#### Remediation Permissions (16)

| Permission | Service | Remediation Use Case |
|-----------|---------|---------------------|
| `Microsoft.Authorization/roleAssignments/write` | IAM | Create role assignments (managed identity setup) |
| `Microsoft.Authorization/roleAssignments/delete` | IAM | Remove stale or unknown-object role assignments |
| `Microsoft.Compute/virtualMachines/write` | Compute | Assign managed identity to VMs |
| `Microsoft.Compute/virtualMachines/extensions/write` | Compute | Migrate VM extensions from SAS to managed identity |
| `Microsoft.Network/networkSecurityGroups/securityRules/write` | Network | Patch overly permissive NSG rules |
| `Microsoft.Network/networkSecurityGroups/securityRules/delete` | Network | Remove overly permissive NSG rules |
| `Microsoft.Storage/storageAccounts/write` | Storage | Disable shared key, set SAS policy, restrict network access |
| `Microsoft.Storage/storageAccounts/regenerateKey/action` | Storage | Rotate keys after secret exposure |
| `Microsoft.Storage/storageAccounts/blobServices/containers/write` | Storage | Set public containers to private |
| `Microsoft.Insights/diagnosticSettings/write` | Monitor | Enable diagnostic logging |
| `Microsoft.Web/sites/config/write` | App Service | Enable authentication, add access restrictions |
| `Microsoft.ApiManagement/service/backends/write` | API Management | Update APIM backend configuration |
| `Microsoft.ApiManagement/service/apis/write` | API Management | Update API auth policies |
| `Microsoft.ApiManagement/service/namedValues/write` | API Management | Migrate secrets to Key Vault references |
| `Microsoft.KeyVault/vaults/accessPolicies/write` | Key Vault | Grant access for APIM managed identity |
| `Microsoft.KeyVault/vaults/secrets/write` | Key Vault | Create secrets during Key Vault migration |

#### Role Definitions

See [custom-role.json](custom-role.json) for the complete JSON definition.
Deploy at the appropriate scope:

| Scope | Assignable Scope Value |
|-------|----------------------|
| Subscription | `/subscriptions/<subscription-id>` |
| Management Group | `/providers/Microsoft.Management/managementGroups/<management-group-id>` |

---

## Entra ID Permissions

| Role | Purpose |
|------|---------|
| [**Global Reader**](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#global-reader) | Full read-only access to all Entra ID objects — required for CIEM alert investigation and identity-aware remediation decisions |

> **Guest user remediation** additionally requires the Microsoft Graph application permission `User.ReadWrite.All` on the App Registration. This is a Graph API permission, not an Azure RBAC role — configure it under **App Registration → API Permissions** in the Azure Portal.

---

## Implementation Checklist

This checklist assumes [Assisted-Remediation](../Assisted-Remediation/README.md) Method 1
(Bicep template) has already been deployed, creating the `TamnoonFederationApp` Service Principal.

| Step | Action | Who |
|------|--------|-----|
| 1 | Verify Assisted-Remediation deployment is complete — `TamnoonFederationApp` SPN exists with Reader, Storage Blob Data Reader, Log Analytics Reader, Directory Readers | Customer |
| 2 | Choose remediation approach: **Option 1** (built-in roles) or **Option 2** (custom role) | Customer + Tamnoon |
| 3a | *If Option 1:* Assign Contributor + User Access Administrator to the SPN at desired scope | Customer |
| 3b | *If Option 2:* Create custom role from [custom-role.json](custom-role.json) at desired scope | Customer |
| 4 | Assign the chosen role(s) to the `TamnoonFederationApp` Service Principal | Customer |
| 5 | Assign [Global Reader](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#global-reader) Entra ID directory role to the SPN | Customer |
| 6 | *(Optional)* Grant `User.ReadWrite.All` Graph API permission for guest user remediation | Customer |
| 7 | Validate — Tamnoon runs remediation workflows in dry-run mode to confirm access | Tamnoon |

---

## Permissions Summary

| Layer | Investigation (Assisted-Remediation) | Full-Remediation (this document) |
|-------|--------------------------------------|----------------------------------|
| Azure RBAC — Built-in | Reader, Storage Blob Data Reader, Log Analytics Reader | + Contributor & User Access Admin (Option 1) |
| Azure RBAC — Custom | 15 investigation permissions | + 16 remediation permissions (Option 2) |
| Entra ID — Directory Role | Directory Readers | + Global Reader |
| Microsoft Graph | — | + `User.ReadWrite.All` *(optional, guest remediation)* |

## Support

For help configuring remediation permissions, contact your Tamnoon
CloudPros integration engineer.

Maintained by: [tamnoon.io](https://tamnoon.io)
