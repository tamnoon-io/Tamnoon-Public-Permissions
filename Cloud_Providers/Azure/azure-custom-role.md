# Tamnoon CloudPros – Azure Custom Roles

The built-in **Reader**, **Reader & Data Access**, and **Log Analytics Reader** roles allows Tamnoon Service Engineering to investigate alerts without broad write privileges, while other investigative tasks require finer-grained permissions. To address these gaps, we've defined a tailored Azure Custom Role that grants exactly the additional rights needed for our investigation and remediation workflows. This Custom Role is designed to evolve over time, ensuring compatibility with Azure API changes and the expanding array of services supported by Tamnoon.

---

## 1 · Subscription-Scoped Role

### Role JSON

```jsonc
{
  "Name": "Tamnoon Custom Role",
  "IsCustom": true,
  "Description": "Tamnoon Custom Role Permissions (subscription scope).",
  "Actions": [
    "Microsoft.Web/sites/functions/read",
    "Microsoft.Web/sites/config/read",
    "Microsoft.Web/sites/config/list/action",
    "Microsoft.Web/sites/host/listKeys/action",
    "Microsoft.Web/sites/functions/listKeys/action",
    "Microsoft.Storage/storageAccounts/listKeys/action",
    "Microsoft.KeyVault/vaults/keys/read",
    "Microsoft.KeyVault/vaults/secrets/readMetadata/action",
    "Microsoft.KeyVault/vaults/certificates/read"
    "Microsoft.Insights/logs/read",
    "Microsoft.Insights/DiagnosticSettings/read"

  ],
  "NotActions": [],
  "DataActions": [],
  "NotDataActions": [],
  "AssignableScopes": [
    "/subscriptions/<subscription-id>"
  ]
}
```
----

# 2. Management-Group-Scoped Role
```jsonc
{
  "Name": "Tamnoon Custom Role",
  "IsCustom": true,
  "Description": "Tamnoon Custom Role Permissions (management-group scope).",
  "Actions": [
    "Microsoft.Web/sites/functions/read",
    "Microsoft.Web/sites/config/read",
    "Microsoft.Web/sites/config/list/action",
    "Microsoft.Web/sites/host/listKeys/action",
    "Microsoft.Web/sites/functions/listKeys/action",
    "Microsoft.Storage/storageAccounts/listKeys/action",
    "Microsoft.KeyVault/vaults/keys/read",
    "Microsoft.KeyVault/vaults/secrets/readMetadata/action",
    "Microsoft.KeyVault/vaults/certificates/read"
    "Microsoft.Insights/logs/read",
    "Microsoft.Insights/DiagnosticSettings/read"
  ],
  "NotActions": [],
  "DataActions": [],
  "NotDataActions": [],
  "AssignableScopes": [
    "/providers/Microsoft.Management/managementGroups/<mg-id>"
  ]
}
```