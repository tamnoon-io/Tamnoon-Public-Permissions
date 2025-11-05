# Tamnoon Cloud Experts — OCI Read-Only Permissions

Tamnoon recommends creating a dedicated **OCI IAM Group** named **`TamnoonReadOnly`** and assigning a set of **read-only policies** that allow Tamnoon’s tools to safely access and analyze your Oracle Cloud resources without making any changes.

---

## Overview

These policies grant **read-only access** to your tenancy and related services — including Compute, Object Storage, Logging, Monitoring, Cloud Guard, and more.

You can create the group and assign these policies using either:

- ** Option 1:** [OCI Console](#-option-1-create-using-the-oci-console)  
- ** Option 2:** [OCI Cloud Shell (CLI)](#-option-2-create-using-oci-cloud-shell-cli)

---

## Option 1: Create Using the OCI Console

1. **Sign in** to the [Oracle Cloud Console](https://cloud.oracle.com/).
2. Navigate to **Identity & Security → Groups**.
3. Click **Create Group**, and enter:
   - **Name:** `TamnoonReadOnly`  
   - **Description:** `Read-only access group for Tamnoon Cloud Experts`
4. Go to **Identity & Security → Policies**.
5. Click **Create Policy**:
   - **Name:** `TamnoonReadOnlyPolicy`  
   - **Description:** `Provides read-only access for Tamnoon tools`
   - **Compartment:** *Select the root compartment (tenancy)*  
6. Copy and paste the following **policy statements** into the policy editor:

```text
Allow group TamnoonReadOnly to read all-resources in tenancy
Allow group TamnoonReadOnly to read compartments in tenancy
Allow group TamnoonReadOnly to read objectstorage-namespaces in tenancy
Allow group TamnoonReadOnly to read buckets in tenancy
Allow group TamnoonReadOnly to read objects in tenancy
Allow group TamnoonReadOnly to read log-groups in tenancy
Allow group TamnoonReadOnly to read log-content in tenancy
Allow group TamnoonReadOnly to read audit-events in tenancy
Allow group TamnoonReadOnly to read metrics in tenancy
Allow group TamnoonReadOnly to read orm-stacks in tenancy
Allow group TamnoonReadOnly to read orm-jobs in tenancy
Allow group TamnoonReadOnly to read orm-config-source-providers in tenancy
Allow group TamnoonReadOnly to read functions-family in tenancy
Allow group TamnoonReadOnly to read api-gateway-family in tenancy
Allow group TamnoonReadOnly to read cloud-guard-family in tenancy
Allow group TamnoonReadOnly to read usage-budgets in tenancy
Allow group TamnoonReadOnly to read usage-reports in tenancy
Allow group TamnoonReadOnly to read limits in tenancy
Allow group TamnoonReadOnly to read subscriptions in tenancy
Allow group TamnoonReadOnly to read cluster-family in tenancy
Allow group TamnoonReadOnly to use cloud-shell in tenancy
```

7. Click **Create** to finalize the policy.

---

## Option 2: Create Using OCI Cloud Shell (CLI)

If you prefer automation, use **OCI Cloud Shell** or your local OCI CLI to create the group and policy programmatically.

### Create the Group
```bash
oci iam group create   --name TamnoonReadOnly   --description "Read-only access group for Tamnoon Cloud Experts"
```

### Create the Policy
```bash
oci iam policy create   --name TamnoonReadOnlyPolicy   --compartment-id $(oci iam compartment list --access-level ACCESSIBLE --query "data[?\"compartment-id\" == null].id | [0]" --raw-output)   --description "Provides read-only access for Tamnoon tools"   --statements '[
    "Allow group TamnoonReadOnly to read all-resources in tenancy",
    "Allow group TamnoonReadOnly to read compartments in tenancy",
    "Allow group TamnoonReadOnly to read objectstorage-namespaces in tenancy",
    "Allow group TamnoonReadOnly to read buckets in tenancy",
    "Allow group TamnoonReadOnly to read objects in tenancy",
    "Allow group TamnoonReadOnly to read log-groups in tenancy",
    "Allow group TamnoonReadOnly to read log-content in tenancy",
    "Allow group TamnoonReadOnly to read audit-events in tenancy",
    "Allow group TamnoonReadOnly to read metrics in tenancy",
    "Allow group TamnoonReadOnly to read orm-stacks in tenancy",
    "Allow group TamnoonReadOnly to read orm-jobs in tenancy",
    "Allow group TamnoonReadOnly to read orm-config-source-providers in tenancy",
    "Allow group TamnoonReadOnly to read functions-family in tenancy",
    "Allow group TamnoonReadOnly to read api-gateway-family in tenancy",
    "Allow group TamnoonReadOnly to read cloud-guard-family in tenancy",
    "Allow group TamnoonReadOnly to read usage-budgets in tenancy",
    "Allow group TamnoonReadOnly to read usage-reports in tenancy",
    "Allow group TamnoonReadOnly to read limits in tenancy",
    "Allow group TamnoonReadOnly to read subscriptions in tenancy",
    "Allow group TamnoonReadOnly to read cluster-family in tenancy",
    "Allow group TamnoonReadOnly to use cloud-shell in tenancy"
  ]'
```

This command automatically:
- Creates a new **TamnoonReadOnlyPolicy**
- Attaches all recommended **read-only statements**
- Places the policy at the **tenancy level**

---

## Verification

After creating the group and policy:

1. Navigate to **Identity & Security → Groups**.
2. Open the `TamnoonReadOnly` group.
3. Verify that the **TamnoonReadOnlyPolicy** is listed under **Attached Policies**.

---

## References

- [Oracle Cloud IAM Policy Syntax](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policysyntax.htm)
- [Managing Policies in OCI](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingpolicies.htm)
- [Using OCI CLI](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm)
