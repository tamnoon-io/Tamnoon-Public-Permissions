# Tamnoon CloudPros – Azure Custom Roles

The built-in **Reader**, **Reader & Data Access**, and **Log Analytics Reader** roles allow Tamnoon Service Engineering to investigate alerts without broad write privileges, while other investigative tasks require finer-grained permissions.

**Environment-Specific Behavior**
Azure CloudShell: Investigation Scripts execute successfully with only Reader role due to enhanced authentication context. This is from real-world testing, and we acknowledge no official Azure documentation confirms it. Any investigation ran outside Azure CloudShell environment will return expected 403 errors.  

To address these gaps, we've defined a tailored Azure Custom Role that grants exactly the additional rights needed for our investigation and remediation workflows. This Custom Role is designed to evolve over time, ensuring compatibility with Azure API changes and the expanding array of services supported by Tamnoon.

---

## 1 · Subscription-Scoped Role

### Role JSON

```jsonc
{
  "Name": "Tamnoon Custom Role",
  "IsCustom": true,
  "Description": "Tamnoon Custom Role Permissions (subscription scope).",
  "Actions": [
    "Microsoft.Storage/storageAccounts/listKeys/action",
    "Microsoft.OperationalInsights/workspaces/analytics/query/action",
    "Microsoft.OperationalInsights/workspaces/search/action"
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
    "Microsoft.Storage/storageAccounts/listKeys/action",
    "Microsoft.OperationalInsights/workspaces/analytics/query/action",
    "Microsoft.OperationalInsights/workspaces/search/action"
  ],
  "NotActions": [],
  "DataActions": [],
  "NotDataActions": [],
  "AssignableScopes": [
    "/providers/Microsoft.Management/managementGroups/<mg-id>"
  ]
}
```


**Permissions Specifications**
`Microsoft.Storage/storageAccounts/listKeys/action`
Required for: Storage account security analysis scripts (comprehensive container, file share, queue, and table analysis). Retrieving of storage account access keys for data plane operations to determine actual content, public access levels, and security configurations



`Microsoft.OperationalInsights/workspaces/analytics/query/action`
Used for Log Analytics query features in security monitoring scripts. Execution of KQL queries against Log Analytics workspaces for access pattern analysis and security event correlation. 

Alternative: **Log Analytics Reader**

`Microsoft.OperationalInsights/workspaces/search/action`
Used for Log Analytics search capabilities in security analysis. Provides search functionality within Log Analytics workspace data for security investigation. 

Alternative: **Log Analytics Reader**