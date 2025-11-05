# Tamnoon Cloud Experts — AWS Read-Only Permissions (Organization-Wide Deployment)

Tamnoon requires a role in each monitored **AWS account** configured with the **minimum set of read-only permissions** to perform investigations, interrogate cloud resource configurations, and validate activity from log sources.

This guide explains how to deploy the **Tamnoon Trust Role** across **all accounts in your AWS Organization** using an **AWS CloudFormation StackSet**.

---

## Overview

Tamnoon provides a CloudFormation template, **`tamnoon-aws-trust-role.yaml`**, that creates a read-only **trust role** with a strict permissions boundary and AWS-managed read-only policies.  

Using a **StackSet**, you can automatically deploy this role to **every account** in your organization — ensuring consistent access configuration across all managed accounts.

You can deploy the StackSet using either:

- ** Option 1:** [AWS Management Console](#-option-1-deploy-stackset-using-aws-management-console)
- ** Option 2:** [AWS CloudShell / CLI](#-option-2-deploy-stackset-using-aws-cloudshell--cli)

---

## Option 1: Deploy StackSet Using AWS Management Console

1. Sign in to the [AWS Management Console](https://console.aws.amazon.com/).
2. Navigate to **CloudFormation → StackSets**.
3. Click **Create StackSet → With new resources (standard)**.
4. Under **Specify template**, select **Upload a template file**.
5. Upload the file [`tamnoon-aws-trust-role.yaml`](tamnoon-aws-trust-role.yaml).
6. Click **Next**.
7. Under **StackSet details**, enter:
   - **StackSet name:** `tamnoon-readonly-role-org`
   - **TrustedPrincipalArn:** The ARN of the principal that Tamnoon will use for authentication (e.g., your Okta or SSO group).
8. Click **Next**, then under **Deployment targets** select:
   - **Deploy to AWS Organization.**
   - Optionally choose to **exclude specific accounts** if needed.
9. Choose the **Regions** where the stack should deploy (for global IAM roles, one region such as `us-east-1` is sufficient).
10. Review all settings and click **Submit**.

Once complete, AWS CloudFormation will automatically deploy the **Tamnoon Trust Role** to all accounts in your organization.

---

## 🧑‍💻 Option 2: Deploy StackSet Using AWS CloudShell / CLI

If you prefer automation, you can deploy the StackSet directly from **AWS CloudShell** or your local **AWS CLI**.

### 1. Upload or reference the CloudFormation template

Make sure the `tamnoon-aws-trust-role.yaml` file is accessible locally or from an S3 bucket.

### 2. Create the StackSet

```bash
aws cloudformation create-stack-set   --stack-set-name tamnoon-readonly-role-org   --template-body file://tamnoon-aws-trust-role.yaml   --parameters ParameterKey=TrustedPrincipalArn,ParameterValue=arn:aws:iam::<YOUR_ORG_ID>:role/<YOUR_SSO_ROLE>   --capabilities CAPABILITY_NAMED_IAM   --permission-model SERVICE_MANAGED   --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=false
```

This command creates a **service-managed StackSet**, which automatically handles new and removed accounts in your AWS Organization.

### 3. Deploy the StackSet Instances

```bash
aws cloudformation create-stack-instances   --stack-set-name tamnoon-readonly-role-org   --deployment-targets OrganizationalUnitIds=<YOUR_ROOT_OR_OU_ID>   --regions us-east-1
```

This deploys the **Tamnoon Trust Role** across all AWS accounts in the specified Organization Unit (or the entire Org Root).

---

## Role Details

The stack creates a role named **`tamnoon-trust-role`** with the following properties:

- **Trusts:** the principal ARN you provide (`TrustedPrincipalArn` parameter)
- **Attached AWS Managed Policies:**
  ```text
  arn:aws:iam::aws:policy/SecurityAudit
  arn:aws:iam::aws:policy/job-function/ViewOnlyAccess
  arn:aws:iam::aws:policy/IAMReadOnlyAccess
  arn:aws:iam::aws:policy/CloudWatchLogsReadOnlyAccess
  arn:aws:iam::aws:policy/AWSLambda_ReadOnlyAccess
  arn:aws:iam::aws:policy/AWSCloudFormationReadOnlyAccess
  arn:aws:iam::aws:policy/AmazonWorkSpacesWebReadOnly
  arn:aws:iam::aws:policy/AmazonWorkSpacesThinClientReadOnlyAccess
  arn:aws:iam::aws:policy/IAMAccessAnalyzerReadOnlyAccess
  arn:aws:iam::aws:policy/AWSCloudTrail_ReadOnlyAccess
  ```

It also includes two inline policies:

### AllowCloudShell
```yaml
Action: cloudshell:*
Resource: "*"
Condition:
  StringEqualsIfExists:
    cloudshell:environment-id: '${aws:RequestTag/cloud-shell-environment-id}'
```

### AllowExtraPermissions
```yaml
Action:
  - apigateway:Get*
  - aps:ListWorkspaces
  - eks:AccessKubernetesApi
  - account:Get*
  - account:List*
Resource: "*"
```

---

## Permissions Boundary

The StackSet also creates a **Permissions Boundary Managed Policy** that prevents privilege escalation by denying actions such as:

```yaml
iam:CreateRole
iam:AttachRolePolicy
iam:PassRole
iam:UpdateRole
iam:DeleteRole
iam:PutUserPolicy
...
```

This ensures Tamnoon’s role cannot modify or escalate privileges beyond its intended read-only scope.

---

## Verification

After deployment:

1. Go to **AWS CloudFormation → StackSets**.
2. Verify that the **tamnoon-readonly-role-org** StackSet shows **“SUCCEEDED”** in all target accounts.
3. In one or more target accounts:
   - Navigate to **IAM → Roles**.
   - Confirm that **`tamnoon-trust-role`** exists.
   - Verify attached managed and inline policies match the above list.
   - Check that the **Permissions Boundary** is applied.

---

## References

- [AWS CloudFormation StackSets Documentation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-concepts.html)
- [AWS IAM Policies Reference](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html)
- [AWS CloudShell User Guide](https://docs.aws.amazon.com/cloudshell/latest/userguide/what-is-aws-cloudshell.html)
