# Tamnoon CloudPros — Azure Custom Role

The built-in [Reader](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/general#reader), [Storage Blob Data Reader](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/storage#storage-blob-data-reader), and [Log Analytics Reader](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/manage-access?tabs=portal#log-analytics-reader) roles cover the majority of investigation workflows. Some tasks require finer-grained permissions — this custom role grants exactly the additional rights needed.

> **CloudShell note:** Investigation scripts execute successfully with only the Reader role inside Azure CloudShell due to its enhanced authentication context. Outside CloudShell, the permissions below are required to avoid 403 errors.

---

## Permissions

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

---

## 1. Subscription-Scoped Role

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

## 2. Management-Group-Scoped Role

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

---

This role should be maintained to reflect evolving API capabilities and the expanding array of services supported by Tamnoon.
