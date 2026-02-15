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
| `roles/iam.securityReviewer` | View IAM policies at organization, folder, and project levels (role visibility for all identities across hierarchy) |
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
| `roles/iam.securityReviewer` | View IAM policies at folder and project levels (role visibility for all identities across hierarchy) |
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

The following IAM investigation capabilities are available through `roles/viewer` and `roles/iam.securityReviewer`:

| Capability | Permissions Included | Notes |
|------------|---------------------|-------|
| **Deny Policies** | `iam.denypolicies.get`, `iam.denypolicies.list` | Via `roles/viewer` — view deny policies blocking permissions |
| **Role Definitions** | `iam.roles.get`, `iam.roles.list` | Via `roles/viewer` — enumerate permissions in roles |
| **Principal Access Boundaries** | `iam.principalaccessboundarypolicies.get`, `iam.principalaccessboundarypolicies.list` | Via `roles/viewer` — view PAB policies limiting resource access |
| **IAM Recommender** | `recommender.iamPolicyRecommendations.get`, `recommender.iamPolicyRecommendations.list`, `recommender.iamServiceAccountInsights.get`, `recommender.iamServiceAccountInsights.list` | Via `roles/viewer` — unused permissions and service account activity insights |
| **Policy Analyzer** | `policyanalyzer.serviceAccountLastAuthenticationActivities.query`, `policyanalyzer.serviceAccountKeyLastAuthenticationActivities.query`, `policyanalyzer.resourceAuthorizationActivities.query` | Via `roles/viewer` — query actual permission usage |
| **Service Accounts** | `iam.serviceAccounts.get`, `iam.serviceAccounts.list`, `iam.serviceAccountKeys.get`, `iam.serviceAccountKeys.list` | Via `roles/viewer` — view service account configuration |
| **Project IAM Policies** | `resourcemanager.projects.getIamPolicy` | Via `roles/viewer` — read IAM policy bindings at project level |
| **Folder/Org IAM Policies** | `resourcemanager.folders.getIamPolicy`, `resourcemanager.organizations.getIamPolicy` | Via `roles/iam.securityReviewer` — `roles/viewer` does not include these. Without this, roles granted at folder or org level are invisible for all identities (users, groups, service accounts) |

### Scope-Level Requirements

These roles must be granted at the appropriate scope for full coverage. GCP IAM policies can be attached at organization, folder, or project levels — a role granted only at project level cannot see policies at higher levels.

| Scope | `roles/viewer` enables | `roles/iam.securityReviewer` enables |
|-------|------------------------|--------------------------------------|
| **Organization** | Deny policies, PAB, recommender insights, custom roles at all levels | IAM policy visibility across org, all folders, and all projects |
| **Folder** | Deny policies, PAB, recommender insights within folder scope | IAM policy visibility across folder and contained projects |
| **Project** | Project-level IAM analysis only | Project-level IAM policy reads (already covered by `viewer`) |

**Without org-level access**, IAM investigations are limited to the assigned scope (folder or project), and deny policies, PAB restrictions, or IAM role grants at higher levels cannot be analyzed.

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
| Organization | `roles/viewer`, `roles/iam.securityReviewer`, `roles/logging.privateLogViewer`, `roles/resourcemanager.organizationViewer`, `roles/serviceusage.serviceUsageConsumer` | Full - deny policies, PAB, recommender insights, IAM policy visibility across org/folder/project |
| Folder | `roles/viewer`, `roles/iam.securityReviewer`, `roles/logging.privateLogViewer`, `roles/resourcemanager.folderViewer`, `roles/serviceusage.serviceUsageConsumer` | Partial - folder and project level IAM policy visibility, deny policies, PAB |
| Project | `roles/viewer`, `roles/logging.privateLogViewer`, `roles/serviceusage.serviceUsageConsumer` | Limited - project level only (no folder/org IAM policy visibility) |
