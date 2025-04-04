Tamnoon CloudPros require specific Microsoft Entra ID permissions to analyze identity and access management (IAM) misconfigurations and cloud infrastructure entitlement management (CIEM) issues affecting both human and non-human identities. 

Microsoft Entra ID (formerly known as Azure Active Directory) permissions are granted using Microsoft Entra ID Directory Roles. Directory Roles grant access to Microsoft Entra ID resources such as Users, Groups, Service Principals (SPN)/App Registrations and Applications.

Permissions Management is an optional CIEM (Cloud Infrastructure and Entitlements Management) module of Microsoft Entra ID that provides comprehensive visibility into permissions assigned to all identities—including over-privileged workload and user identities, actions, and resources—across multicloud infrastructures such as Microsoft Azure, Amazon Web Services (AWS), and Google Cloud Platform (GCP). The solution detects, automatically right-sizes, and continuously monitors unused and excessive permissions, thereby enhancing Zero Trust security strategies by enforcing the principle of least privilege access.
- If enabled, Tamnoon can leverage Permissions Management to enhance the ability to detect and respond to CIEM alerts.

The preferred role is the **Global Reader** role.

https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#global-reader

At a minimum, Tamnoon requires the **Directory Readers** role across assigned scopes. 

https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#directory-readers

**Entra Permissions Management** :

To use the Entra Permissions Management module, Tamnoon requires either the **Global Reader** role or a custom role with `microsoft.permissionsManagement/allEntities/allProperties/read` permissions.
