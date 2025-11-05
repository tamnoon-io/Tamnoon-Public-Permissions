# Tamnoon Cloud Experts — Orca Security Role Requirements

Tamnoon integrates with **Orca Security** to enhance cloud visibility and risk analytics across customer environments.  
To enable seamless, read-only integration, specific roles must be assigned to Tamnoon CloudPro users within your Orca Security platform.

---

## Overview

The integration between **Tamnoon CloudPro** and **Orca Security** provides secure, visibility-driven access to your Orca environment.  
Tamnoon uses this connection to review security posture, analyze alert data, and assess resource configurations — without requiring administrative or write-level privileges.

Tamnoon does **not** perform configuration changes or enforcement actions. Access is limited strictly to reading alerts and posture information.

---

## Required Role for Tamnoon CloudPro Users

Assign the following **Orca Security role** to all users or service accounts that Tamnoon will use for integration and analysis:

| Role Name | Purpose |
|------------|----------|
| **Alert Reviewer** | Provides Tamnoon CloudPro with read-only access to view, filter, and analyze security alerts, misconfigurations, and compliance findings within Orca Security. |

---

## Access Philosophy

Tamnoon adheres to the **principle of least privilege**, requesting only the permissions required to read and evaluate alert and posture data within Orca Security.  
This ensures secure integration while preserving strict control of administrative rights and preventing any modification of monitored resources.

Assigning the **Alert Reviewer** role enables Tamnoon to collect the visibility data needed to support continuous security assessments and incident correlation across your connected cloud environments.

---

## Notes

- Assign the role to the **Tamnoon CloudPro user(s)** or **service principal** created for integration within your Orca Security tenant.  
- Ensure that the role scope covers all connected cloud accounts that Tamnoon is expected to monitor.  
- Permissions may take several minutes to propagate across the Orca Security console and APIs after assignment.

---

## References

- [Orca Security Documentation](https://docs.orcasecurity.io/)
- [Orca Security Roles and Permissions](https://docs.orcasecurity.io/docs/roles-and-permissions)
