<img src="images/Tamnoon.png" width="470">

# Tamnoon Onboarding - GCP Permissions Reference

This document provides an overview of Google Cloud Platform (GCP) roles needed by GCP Users and/or Service Accounts created for Tamnoon CloudPros, to access your GCP Projects through GCP console, or programmatically. Associated permissions cover the majority of investigation playbooks, resource-listing operations, and log analysis via portal or API.

--------------------------------
## 1. Organization-Level Onboarding
--------------------------------
Permission requirement from this section applies if/when GCP organization wide onboarding is in scope.
Sections 2. and 3. not applicable because of permissions inheritance.

| Role | Purpose |
|------|---------|
| `roles/resourcemanager.organizationViewer` | View organization metadata and hierarchy structure |
| `roles/viewer` | Read-only access to all resources, IAM policies, and recommender insights |
| `roles/logging.privateLogViewer` | Access to Data Access Logs and filtered log views |
| `roles/serviceusage.serviceUsageConsumer` | View enabled APIs and service usage quotas |

-----------------------------
## 2. Folder-Level Onboarding
-----------------------------
This only applies when customer decides not to onboard their entire GCP Organization.
All GCP projects within the various folders in scope will be covered.

| Role | Purpose |
|------|---------|
| `roles/resourcemanager.folderViewer` | View folder metadata and contained projects |
| `roles/viewer` | Read-only access to all resources, IAM policies, and recommender insights |
| `roles/logging.privateLogViewer` | Access to Data Access Logs and filtered log views |
| `roles/serviceusage.serviceUsageConsumer` | View enabled APIs and service usage quotas |

---------------------------------
## 3. Project-Level Onboarding
---------------------------------

| Role | Purpose |
|------|---------|
| `roles/viewer` | Read-only access to all resources, IAM policies, and recommender insights |
| `roles/logging.privateLogViewer` | Access to Data Access Logs and filtered log views |
| `roles/serviceusage.serviceUsageConsumer` | View enabled APIs and service usage quotas |


---

## IAM Investigation Permissions

When `roles/viewer` is assigned, the following IAM investigation capabilities are included:

| Capability | Permissions Included | Notes |
|------------|---------------------|-------|
| **Deny Policies** | `iam.denypolicies.get`, `iam.denypolicies.list` | View deny policies blocking permissions |
| **Role Definitions** | `iam.roles.get`, `iam.roles.list` | Enumerate permissions in roles |
| **Principal Access Boundaries** | `iam.principalaccessboundarypolicies.get`, `iam.principalaccessboundarypolicies.list` | View PAB policies limiting resource access |
| **IAM Recommender** | `recommender.iamPolicyRecommendations.get`, `recommender.iamPolicyRecommendations.list`, `recommender.iamServiceAccountInsights.get`, `recommender.iamServiceAccountInsights.list` | Unused permissions and service account activity insights |
| **Policy Analyzer** | `policyanalyzer.serviceAccountLastAuthenticationActivities.query`, `policyanalyzer.serviceAccountKeyLastAuthenticationActivities.query`, `policyanalyzer.resourceAuthorizationActivities.query` | Query actual permission usage |
| **Service Accounts** | `iam.serviceAccounts.get`, `iam.serviceAccounts.list`, `iam.serviceAccountKeys.get`, `iam.serviceAccountKeys.list` | View service account configuration |

### Organization-Level Requirement for IAM Investigations

For complete IAM analysis across the GCP hierarchy, `roles/viewer` must be granted at **Organization Level**. This enables:

- **Deny Policy Analysis**: Deny policies can be attached at organization, folder, or project levels. Org-level access ensures visibility into all deny policies that may affect principals.
- **Principal Access Boundary Analysis**: PAB policies are typically defined at org-level and restrict which resources principals can access.
- **IAM Recommender Insights**: Cross-project permission usage analysis requires org-level access for complete recommendations.
- **Custom Role Visibility**: Organization-scoped custom roles are only visible with org-level access.

**Without org-level access**, IAM investigations are limited to the assigned scope (folder or project), and deny policies or PAB restrictions at higher levels cannot be analyzed.

---

## Custom Roles

### Custom Logs Viewer for Tamnoon CloudPro

Should `roles/logging.privateLogViewer` not be assigned, Tamnoon recommends creating the below GCP Custom Role at **GCP Organization Level**.

| Permission | Purpose |
|------------|---------|
| `logging.privateLogEntries.list` | Read data access and audit logs |
| `logging.views.access` | Access filtered log views |
| `logging.locations.get` | Read log storage location configuration |
| `logging.locations.list` | Enumerate available log storage regions |
| `resourcemanager.projects.get` | Read project metadata for log correlation |

**Note:** `observability.scopes.get` is already included in `roles/viewer` and does not need to be added to the custom role.

---

## API Requirements

The following GCP APIs must be enabled for full functionality:

| API | Purpose |
|-----|---------|
| Cloud Resource Manager API | Project/folder/org hierarchy traversal |
| IAM API | Role and permission analysis |
| Recommender API | IAM policy recommendations and insights |
| Policy Analyzer API | Permission usage activity analysis |
| Cloud Logging API | Audit log access |

---

## Summary

| Scope | Required Roles | IAM Investigation Capability |
|-------|----------------|------------------------------|
| Organization | `roles/viewer`, `roles/logging.privateLogViewer`, `roles/resourcemanager.organizationViewer`, `roles/serviceusage.serviceUsageConsumer` | Full - all deny policies, PAB, recommender insights |
| Folder | `roles/viewer`, `roles/logging.privateLogViewer`, `roles/resourcemanager.folderViewer`, `roles/serviceusage.serviceUsageConsumer` | Partial - folder and project level only |
| Project | `roles/viewer`, `roles/logging.privateLogViewer`, `roles/serviceusage.serviceUsageConsumer` | Limited - project level only |
