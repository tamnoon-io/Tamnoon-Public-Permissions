# Tamnoon CloudPros – Azure Built-in Roles

The below Built-in Azure RBAC Roles are needed by Entra ID Users and/or Service Principal created for Tamnoon CloudPros, to access your Azure Subscription(s) through Azure Console, or programmatically.
Associated permissions cover the majority of investigation playbooks, resource-listing operations, and log analysis via portal or API.

- **Reader**
https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/general#reader

- **Storage Blob Data Reader** (For reading diagnostic logs stored in Storage Account blob containers)
https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/storage#storage-blob-data-reader

- **Log Analytics Reader** (Preferred Option for Audit Logs Access, Activity Log, NSG Flow Logs Analysis, etc… investigation related automations.)
https://learn.microsoft.com/en-us/azure/azure-monitor/logs/manage-access?tabs=portal#log-analytics-reader

---

## Role Comparison: Storage Blob Data Reader vs Reader and Data Access

| Capability | Storage Blob Data Reader | Reader and Data Access |
|------------|-------------------------|------------------------|
| Read blob data | ✓ | ✓ |
| Read file/queue/table data | ✗ | ✓ |
| List storage keys (`listKeys/action`) | ✗ | ✓ |
| Auth method | Azure AD only | Key-based or Azure AD |

**Why Storage Blob Data Reader?**
- Least-privilege: Cannot access storage account keys
- Sufficient for reading diagnostic logs (stored as blobs in `insights-logs-*` containers)
- More secure: Uses Azure AD authentication only
