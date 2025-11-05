# Tamnoon Cloud Experts — Wiz Role Requirements

Tamnoon integrates with **Wiz** to deliver enhanced cloud visibility, configuration analytics, and security posture assessment.  
Wiz uses a flexible Role-Based Access Control (RBAC) model with multiple constructs to define effective permissions.  
The information in this guide is derived from both the **Wiz console** and the [Role-Based Access Control (RBAC) documentation](https://docs.wiz.io/wiz-docs/docs/role-based-access-control?lng=en#role-permissions).

---

## Overview

To enable Tamnoon’s cloud analysis capabilities within Wiz, specific **roles and scopes** must be assigned depending on the type of Tamnoon subscription and how the customer organizes projects and authentication.

Tamnoon CloudPro requires only the permissions necessary for read and response operations within Wiz — never full administrative access.  
Assignments are made according to **Tamnoon service tier** and **project scope**.

---

## Required Roles for Tamnoon CloudPro Users

When setting up permissions for Tamnoon in Wiz, gather the following information to determine the correct role assignments.

### 1. Authentication Method

| Authentication Type | Description |
|----------------------|-------------|
| **Identity Provider (IDP)** | The customer provisions a user for each Tamnoon TSE per their own identity management process (e.g., Okta, Azure AD). |
| **Wiz Authentication** | Tamnoon automation creates users through the Wiz API for managed onboarding. |

### 2. Role Assignments by Subscription and Scope

| Tamnoon Subscription | Wiz Scope | Required Wiz Role |
|-----------------------|-----------|-------------------|
| **Assisted** | **Global** | Global Contributor |
| **Managed** | **Global** | Global Responder |
| **Assisted** | **Project** | Project Member |
| **Managed** | **Project** | Project Admin |

> **Note:** When using Project scopes, ensure that the appropriate role is assigned for **each project or folder** within the Wiz environment.

> **Caution:** Wiz recommends avoiding “horizontally” scoped projects that use tags across multiple cloud subscriptions to define projects, as this can cause permission and mapping inconsistencies.

---

## Key Terms

| Term | Definition |
|------|-------------|
| **User** | Represents a human account within Wiz. Authentication occurs through Wiz or a configured identity provider (e.g., Okta). Users are invited via the Wiz console under **Settings → User Management → Invite User**. |
| **Service Account** | Used for machine-to-machine authentication with the Wiz API. There are two types: **Custom Integration (GraphQL API)** and **Component-specific**. |
| **Custom Integration (GraphQL API)** | Allows customizable permission scopes for integrations and automation scripts. |
| **Component-specific** | Defined by Wiz for built-in components (e.g., Wiz Sensor, Kubernetes Admission Controller). Permissions for these accounts cannot be modified. |
| **User Role** | The mapping between a user and the set of assigned scopes. |
| **Scope** | Defines the actions a user or service account can perform. Scopes may be project-scoped or global, and some aggregate others (e.g., `read:all` includes `read:detections`). |
| **Project** | Represents a subdivision of your cloud estate, typically aligned with an AWS account, GCP project, or Azure subscription. |
| **Folder** | A collection of multiple projects within Wiz, often used for organizing related cloud environments. |

---

## Access Philosophy

Tamnoon follows the **principle of least privilege**, requesting only the roles and scopes necessary to collect configuration, detection, and security posture data.  
Access is scoped appropriately to the **Tamnoon service tier** and **customer Wiz project hierarchy**.

---

## References

- [Wiz Role-Based Access Control (RBAC)](https://docs.wiz.io/wiz-docs/docs/role-based-access-control?lng=en#role-permissions)
- [Wiz User and Service Account Management](https://docs.wiz.io/wiz-docs/docs/user-management)
