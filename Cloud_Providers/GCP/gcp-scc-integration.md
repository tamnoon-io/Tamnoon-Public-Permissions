# GCP Security Command Center Integration

To read and ingest GCP SCC findings into Tamnoon, Integration (GCP service account created for Tamnoon) requires below permissions:

## Organization-Level Permissions
`roles/securitycenter.adminviewer` - Visibility into ALL assets, findings and attack paths in SCC. 

The above GCP built-in roles applies when onboarding customers that have enabled GCP SCC at the Organization-Level;

## Security Command Center Folder-Level Permissions

It is also common to see customers electing to activate SCC on a select few folders i.e. not across the entire GCP Organization. 

`roles/securitycenter.assetsViewer` - Read Access to Security Center Assets
`roles/securitycenter.findingsViewer` - Read Access to Security Center Findings
`roles/securitycenter.attackPathsViewer` - Read Access to Security Center Attack Paths

Note: `roles/securitycenter.attackPathsviewer` cannot be granted at project-level. 