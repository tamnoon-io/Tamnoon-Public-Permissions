# Tamnoon Cloud Experts - Wiz Permissions

Wiz uses different constructs to piece together effective permissions. The content on this page was developed by examining the Wiz console and using the [Role-based Access Control (RBAC) page of Wiz Docs](https://docs.wiz.io/wiz-docs/docs/role-based-access-control?lng=en#role-permissions).

# Wiz Tamnoon Customer Scoping Questions

When scoping permissions for a customer using Wiz as their CNAPP, we must gather three datapoints represented in the two questions below.

<aside>
🔥

“Horizontally” scoped projects that apply tags across two or more cloud subscriptions and use tags to define Wiz Projects have some sharp edges. Wiz recommends against “horizontally” scoped projects.

</aside>

1. **How will Tamnoon TSE authenticate to Wiz?**
    1. **IDP**: The customer provisions a user for each member of their TSE team per their own procedures.
    2. **Wiz**: Tamnoon provides automation that creates the users using the Wiz API.
2. **What Tamnoon subscription (Assisted or Managed) and Wiz scope (Global or Project) will be used?**
    1. **Assisted, Global**: Global Contributor role
    2. **Managed, Global**: Global Responder role
    3. **Assisted, Project**: Project Member role
    4. **Managed, Project**: Project Admin role

<aside>
⚠️

Project Scopes must assign the appropriate role for each project/folder.

</aside>

# Terms

**User**: A user represents a human being with access to Wiz. User authentication occurs either by Wiz or a configured 3rd party identity provider (e.g. Okta). Wiz users are invited from the Wiz console by navigating to Settings - User Management and selecting the Invite User button.

**Service Accounts**: Service accounts are used by machine-to-machine interfaces to authenticate with the Wiz API. There are two types of service accounts: Custom Integration (GraphQL API) and Component-specific. 

**Custom Integration (GraphQL API)** - Customizable permission scopes for use by third-party integrations and custom scripts.
**Component-specific** - Defined by Wiz for use by components such as Wiz Sensor and Kubernetes Admission Controller, so their permissions cannot be edited.

**User Role**: A user role is the mapping between a user the assigned Scopes.

**Scopes**: Scopes are authorizations to perform specific actions in Wiz. Scopes may be “catch-all” scopes that include all permissions underneath them. For example, `read:all` also grants the `read:detections` scope. Scopes may be project-scoped or global.

**Project**: Subdivisions of a cloud estate, usually identified by cloud subscriptions (e.g. AWS account, GCP Project, Azure subscription).

**Folder**: Collection of Projects.