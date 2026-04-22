# Tamnoon GCP Onboarding — gcloud Commands

Raw `gcloud` commands for onboarding the Tamnoon service account with Workload Identity Federation.

Replace the following placeholders before running:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `<identity-project>` | GCP project ID where SA and WIF resources are created | `cust-shared-infra` |
| `<tamnoon-tenant-id>` | Tamnoon tenant ID (UUID, provided during onboarding) | `5104b7b7-56ee-4f51-97d8-0a6c49f846f5` |
| `<project-number>` | Numeric project number of the identity project | `482917305164` |
| `<org-id>` | Organization ID (for organization scope) | `123456789012` |
| `<folder-id>` | Folder ID (for folder scope) | `987654321098` |
| `<project-id>` | Target project ID (for project scope) | `cust-app-prod` |

---

## Step 1: Create Service Account

```bash
gcloud iam service-accounts create tamnoon-federate-svc-account \
  --display-name=tamnoon-federate-svc-account \
  --project=<identity-project>
```

## Step 2: Create Workload Identity Pool

```bash
gcloud iam workload-identity-pools create tamnoon-pool-federate \
  --location=global \
  --display-name=TamnoonWorkloadIdentityPool \
  --project=<identity-project>
```

## Step 3: Create AWS Provider

```bash
gcloud iam workload-identity-pools providers create-aws tamnoon-aws-federate \
  --workload-identity-pool=tamnoon-pool-federate \
  --location=global \
  --account-id=112665896816 \
  --display-name=tamnoon-aws-federate \
  --attribute-mapping="google.subject=assertion.arn,attribute.aws_role=assertion.arn.contains('assumed-role') ? assertion.arn.extract('{account_arn}assumed-role/') + 'assumed-role/' + assertion.arn.extract('assumed-role/{role_name}/') : assertion.arn" \
  --attribute-condition="attribute.aws_role == 'arn:aws:sts::112665896816:assumed-role/gcp-onboarding-trust-<tamnoon-tenant-id>'" \
  --project=<identity-project>
```

## Step 4: Bind WIF Principal to Service Account

First, get the project number:

```bash
PROJECT_NUMBER=$(gcloud projects describe <identity-project> --format='value(projectNumber)')
```

Then create the binding:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  tamnoon-federate-svc-account@<identity-project>.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/tamnoon-pool-federate/attribute.aws_role/arn:aws:sts::112665896816:assumed-role/gcp-onboarding-trust-<tamnoon-tenant-id>" \
  --project=<identity-project>
```

## Step 5: Assign IAM Roles

Choose **one** of the following based on your onboarding scope.

### Organization scope (recommended)

```bash
for role in roles/viewer roles/browser roles/iam.securityReviewer roles/cloudasset.viewer roles/logging.privateLogViewer roles/serviceusage.serviceUsageConsumer; do
  gcloud organizations add-iam-policy-binding <org-id> \
    --member="serviceAccount:tamnoon-federate-svc-account@<identity-project>.iam.gserviceaccount.com" \
    --role="$role" --quiet
done
```

### Folder scope

```bash
# Single folder
FOLDERS="<folder-id>"

# Multiple folders (space-separated)
# FOLDERS="111222333 444555666 777888999"

for folder_id in $FOLDERS; do
  for role in roles/viewer roles/browser roles/iam.securityReviewer roles/cloudasset.viewer roles/logging.privateLogViewer roles/serviceusage.serviceUsageConsumer; do
    gcloud resource-manager folders add-iam-policy-binding "$folder_id" \
      --member="serviceAccount:tamnoon-federate-svc-account@<identity-project>.iam.gserviceaccount.com" \
      --role="$role" --quiet
  done
done
```

### Project scope

```bash
# Single project
PROJECTS="<project-id>"

# Multiple projects (space-separated)
# PROJECTS="cust-app-prod cust-app-staging cust-data-warehouse"

for project_id in $PROJECTS; do
  for role in roles/viewer roles/browser roles/iam.securityReviewer roles/cloudasset.viewer roles/logging.privateLogViewer roles/serviceusage.serviceUsageConsumer; do
    gcloud projects add-iam-policy-binding "$project_id" \
      --member="serviceAccount:tamnoon-federate-svc-account@<identity-project>.iam.gserviceaccount.com" \
      --role="$role" --quiet
  done
done
```

## Step 6: Retrieve Onboarding Output

```bash
PROJECT_NUMBER=$(gcloud projects describe <identity-project> --format='value(projectNumber)')

SA_UNIQUE_ID=$(gcloud iam service-accounts describe \
  tamnoon-federate-svc-account@<identity-project>.iam.gserviceaccount.com \
  --format='value(uniqueId)')

cat <<EOF
{
  "identity_project_number": "$PROJECT_NUMBER",
  "service_account_id": "$SA_UNIQUE_ID",
  "workload_identity_pool_id": "tamnoon-pool-federate",
  "workload_identity_provider_id": "tamnoon-aws-federate"
}
EOF
```

Provide this JSON to Tamnoon via the onboarding UI to complete setup.
