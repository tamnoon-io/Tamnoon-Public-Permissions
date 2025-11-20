# Tamnoon Cloud Experts — Prisma Cloud Role Requirements

Tamnoon integrates with **Prisma Cloud** to collect cloud posture, vulnerability data, configuration metadata, and alerts across customer environments.  
Because Prisma Cloud’s RBAC model is highly segmented, no built-in role matches Tamnoon’s least-privilege access model.

Tamnoon requires a **custom role** and **custom permission group** for safe, read-only visibility.

---

# Recommended Prisma Cloud Role  
**Role Name:** `Tamnoon-ReadOnly`  
**Type:** Custom Role  
**Purpose:** Provide Tamnoon CloudPro with secure, non-destructive, read-only access across Prisma Cloud.

---

# Assigned Permissions

## Dashboard
- Code Security & Application Security Tabs: **View**
- Vulnerability: **View**

## Asset Inventory
- Overview: **View**

## Application Inventory
- Applications: **View**

## Investigate
- Asset: **View**
- Config: **View**
- Audit Events: **View**
- Network: **View**
- Vulnerability: **View**
- Applications: **View**
- Saved Searches: **Create / Delete / View**

## Policies
- Policies: **View**
- Manage Policies Compliance Mapping: **None**

## Compliance
- Standards: **View**
- Overview: **View**
- Reports: **Create / Delete / Update / View**

## Application Security
- Projects: **View**

## Alerts
- Overview: **View**
- Snooze/Dismiss: **None**
- Remediation: **None**
- Rules: **View**
- Reports: **Create / Delete / Update / View**
- Notification Templates: **View**
- Remediate Vulnerabilities: **None**

## Data Security Posture Management
- Data Security Posture Management: **None**

## Data Security
- Data Security Profile: **View**
- Data Security Patterns: **View**
- Data Security Snippet Masking: **View**
- Data Security Resource: **View**
- Data Security Inventory: **View**
- Data Security Dashboard: **View**

## Settings
- Permission Groups: **View**
- Roles: **View**
- Users: **View**
- Access Keys: **None**
- Trusted Login IP Addresses: **View**
- Trusted Alert IP Addresses: **View**
- SSO: **View**
- Audit Logs: **View**
- Cloud Accounts: **View**
- Account Group: **View**
- Resource List: **View**
- Anomaly Trusted List: **View**
- Anomaly Threshold: **View**
- Licensing: **View**
- Integrations: **View**
- Enterprise Settings: **View**
- Providers: **View**
- Application Security: **View**

## Compute
- Cloud Radar: **View**
- Hosts Radar: **View**
- Containers Radar: **View**
- Serverless Radar: **View**
- Code Repositories Vulnerability Policies: **View**
- Images/Containers Vulnerabilities & Compliance Policies: **View**
- Host Vulnerabilities & Compliance Policies: **View**
- Serverless & App-Embedded Runtime Policies: **View**
- Custom Compliance Policies: **View**
- Container Runtime Policies: **View**
- Host Runtime Policies: **View**
- Serverless & App-Embedded Runtime Policies: **View**
- WAAS Policies: **View**
- CNNF Policies: **View**
- Docker Policies: **View**
- Secrets Policies: **View**
- Kubernetes & Admissions Policies: **View**
- Custom Rules: **View**
- Vulnerabilities Dashboard: **View**
- Compliance Dashboard: **View**
- Code Repositories Vulnerabilities & Compliance Results: **View**
- Images/Containers Vulnerabilities & Compliance Results: **View**
- Hosts Vulnerabilities & Compliance Results: **View**
- Serverless & App-Embedded Vulnerabilities & Compliance Results: **View**
- CI Results: **View**
- Container Runtime Results: **View**
- Host Runtime Results: **View**
- Serverless & App-Embedded Runtime Results: **View**
- Runtime Dashboards: **View**
- Image Analysis Sandbox: **View**
- WAAS Events: **View**
- CNNF Runtime Results: **View**
- Docker Runtime Results: **View**
- Kubernetes & Admission Runtime Results: **View**
- Data Updates Pushed to Client Browsers: **View**
- Cloud Account Policy: **None**
- Cloud Discovery Results: **View**
- Logs: **None**
- Defenders Management: **None**
- Alerts: **None**
- Collections and Tags: **None**
- Credentials Store: **None**
- Authentication: **None**
- System: **None**
- System Privileged: **None**
- Utilities: **View**

## Alarm Center
- Alarm Center: **View**
- Alarm Center Settings: **View**

### Action Plans
- Overview: **View**
- Notification Templates: **View**
- Action Plan: **None**
- Remediation & Delegation: **None**

---

# How to Create the Custom Role in Prisma Cloud

## 1. Create the Permission Group
1. Navigate to **Settings → Access Control → Permission Groups**
2. Click **Add → Permission Group**
3. Name it: **`Tamnoon-ReadOnly-Permissions`**
4. Add all permissions listed above at their specified access levels
5. Click **Save**

---

## 2. Create the Custom Role
1. Go to **Settings → Access Control → Roles**
2. Click **Add → Role**
3. Name it: **`Tamnoon-ReadOnly`**
4. Attach the permission group **`Tamnoon-ReadOnly-Permissions`**
5. Assign account scope (recommended: **All Accounts**)
6. Save the role

---

## 3. Assign the Role to Tamnoon Users
1. Navigate to **Settings → Access Control → Users**
2. Select the user(s) or service accounts for Tamnoon CloudPro
3. Add the **Tamnoon-ReadOnly** role
4. Save

---

# Access Philosophy
Tamnoon strictly follows least privilege:
- Read-only visibility  
- No remediation  
- No suppression  
- No asset or account modification  
- No administrative control  

---

# References
- Prisma Cloud Administrator Guide  
- Prisma Cloud RBAC Documentation  
