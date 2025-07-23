# Tamnoon CloudPros Directory Role(s)

The preferred role is the **Global Reader** role.

https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#global-reader

At a minimum, Tamnoon CloudPros require **Directory Readers** 

https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference#directory-readers

Tamnoon CloudPros require specific Microsoft Entra ID permissions to analyze identity and access management (IAM) misconfigurations and cloud infrastructure entitlement management (CIEM) issues affecting both human and non-human identities. 

Microsoft Entra ID (formerly known as Azure Active Directory) permissions are granted using Microsoft Entra ID Directory Roles. Directory Roles grant access to Microsoft Entra ID resources such as Users, Groups, Service Principals (SPN)/App Registrations and Applications.

# Entra Permissions Management
If enabled, Tamnoon can leverage Permissions Management to enhance the ability to detect and respond to CIEM alerts.To use the Entra Permissions Management module, Tamnoon CloudPros require either the **Global Reader** role or a custom role with `microsoft.permissionsManagement/allEntities/allProperties/read` permissions.

Permissions Management solution detects, automatically right-sizes, and continuously monitors unused and excessive permissions, thereby enhancing Zero Trust security strategies by enforcing the principle of least privilege access.

