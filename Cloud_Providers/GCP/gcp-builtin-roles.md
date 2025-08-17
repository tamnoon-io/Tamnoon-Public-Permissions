# Tamnoon Onboarding - GCP Permissions Reference

This document provides an overview of Google Cloud Platform (GCP) roles needed by GCP Users and/or Service Accounts created for Tamnoon CloudPros, to access your GCP Projects through GCP console, or programmatically. Associated permissions cover the majority of investigation playbooks, resource-listing operations, and log analysis via portal or API. 

--------------------------------
## Organization-Level Onboarding
--------------------------------
Permission requirement from this section applies if/when GCP organization wide onboarding is in scope. 
Sections 2. and 3. not applicable because of permissions inheritance. 

### Organization Viewer
`roles/resourcemanager.organizationViewer`

### Viewer
`roles/viewer`

Sufficient for folder-specific monitoring and basic resource visibility.

### Private Logs Viewer
`roles/logging.privateLogViewer`
Essential when Data Access Logs or filtered views are needed at Organization level.

**Custom Logs Viewer for Tamnoon CloudPro**:
Should Private Logs Viewer role not be assigned to Tamnoon CloudPros, Tamnoon recommends creating the below GCP Custom Role with minimum permissions at GCP Organization Level.

- `logging.privateLogEntries.list`
- `logging.views.access`
- `observability.scopes.get`
- `resourcemanager.projects.get` 
- `logging.locations.*` 


### Service Usage Consumer
`roles/serviceusage.serviceUsageConsumer`


-----------------------------
## Folder-Level Onboarding
-----------------------------
This only applies when customer decides not to onboard their entire GCP Organization. 
All GCP projects within the various folders in scope will be covered. 

### Folder Viewer
`roles/resourcemanager.folderViewer`

### Viewer
`roles/viewer`

Sufficient for folder-specific monitoring and basic resource visibility.

### Private Logs Viewer
`roles/logging.privateLogViewer`

This role is essential when Data Access Logs or filtered views are needed at folder level.

**Custom Logs Viewer Role for Tamnoon CloudPro**:
Should Private Logs Viewer role not be assigned to Tamnoon CloudPros, Tamnoon recommends creating the below GCP Custom Role with minimum permissions at GCP Folder Level.

- `logging.privateLogEntries.list` 
- `logging.views.access` 
- `observability.scopes.get` 
- `resourcemanager.projects.get` 
- `logging.locations.*` 

### Service Usage Consumer
`roles/serviceusage.serviceUsageConsumer`


---------------------------------
3. ## Project-Level Onboarding
---------------------------------
### Viewer
`roles/viewer`

Sufficient for project-specific monitoring and basic resource visibility.

### Private Logs Viewer
`roles/logging.privateLogViewer`

**Custom Logs Viewer Role for Tamnoon CloudPro***:
- `logging.privateLogEntries.list`
- `logging.views.access` 
- `observability.scopes.get` 
- `resourcemanager.projects.get` 
- `logging.locations.*` 

Essential when Data Access Logs or filtered views are needed at Project level.

### Service Usage Consumer
`roles/serviceusage.serviceUsageConsumer`


---

