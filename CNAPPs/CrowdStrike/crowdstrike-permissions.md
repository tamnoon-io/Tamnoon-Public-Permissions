# Tamnoon Cloud Experts — CrowdStrike Falcon Role Requirements

Tamnoon integrates with **CrowdStrike Falcon** to provide advanced visibility and analytics across your cloud workloads and security events.  
To ensure Tamnoon’s tools can operate effectively within Falcon, specific **read-only and management roles** must be granted to Tamnoon CloudPro users.

---

## Overview

These roles allow Tamnoon CloudPro to safely **collect configuration data, evaluate security posture**, and **perform non-destructive analysis** within your CrowdStrike Falcon environment.  
Tamnoon does **not** require write, modify, or delete privileges — only the ability to **read configurations, view alerts, and query assets**.

---

## Required Roles for Tamnoon CloudPro Users

Assign the following **Falcon roles** to all users or service accounts that Tamnoon will use for integration and data access:

| Role Name | Purpose |
|------------|----------|
| **Cloud Security Manager** | Enables Tamnoon to view and assess cloud configuration, compliance, and resource posture data. |
| **CSPM Manager** | Grants visibility into CrowdStrike Cloud Security Posture Management (CSPM) findings and recommendations. |
| **Falcon Analyst - Read Only** | Provides read-only access to security detections, dashboards, and event data across your Falcon environment. |
| **Real Time Responder - Read Only Analyst** | Allows limited responder capabilities necessary for Tamnoon to query and validate endpoint telemetry in real time. |

---

## Access Philosophy

Tamnoon follows a **least-privilege principle** — requesting only the roles necessary to perform read-only visibility and security validation.  
No permissions are used for remediation, enforcement, or system changes.

Each of these roles should be assigned to the **Tamnoon CloudPro user(s)**.

---

## Notes

- If your organization uses **role-based access groups** in CrowdStrike Falcon, add Tamnoon CloudPro users to a dedicated group containing the roles above.  
- Ensure that the roles are scoped appropriately to **all cloud environments** you want monitored.  
- Role assignment changes may take several minutes to propagate across the Falcon console and API.

---

## References

- [CrowdStrike Falcon Documentation](https://www.crowdstrike.com/resources/#documentation)
- [CrowdStrike Role-Based Access Control (RBAC) Overview](https://www.crowdstrike.com/blog/tech-center/role-based-access-control/)
