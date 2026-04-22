#!/usr/bin/env python3
"""
Tamnoon GCP Onboarding Script

Creates the Tamnoon service account with Workload Identity Federation (WIF)
and assigns read-only IAM roles at the chosen scope. Supports scope expansion,
reduction, and full offboarding.

Alternative to deploying the tamnoon-io/gcp-onboarding Terraform module
via Infrastructure Manager.

Run in Google Cloud Shell or any environment with gcloud CLI authenticated.

Usage:
    python3 tamnoon_onboarding.py                    # Interactive mode
    python3 tamnoon_onboarding.py --help              # Show help

    # Fresh onboarding
    python3 tamnoon_onboarding.py \\
        --identity-project my-infra-project \\
        --tenant-id 5104b7b7-56ee-4f51-97d8-0a6c49f846f5 \\
        --scope organization --org-id 123456789

    # Expand scope
    python3 tamnoon_onboarding.py \\
        --identity-project my-infra-project \\
        --expand --scope project --project-ids new-proj-a new-proj-b

    # Reduce scope
    python3 tamnoon_onboarding.py \\
        --identity-project my-infra-project \\
        --reduce --scope project --project-ids old-proj-a

    # Offboard
    python3 tamnoon_onboarding.py \\
        --identity-project my-infra-project --offboard
"""

import argparse
import json
import re
import subprocess
import sys

# =============================================================================
# Constants
# =============================================================================

TAMNOON_ROLES = [
    "roles/viewer",
    "roles/browser",
    "roles/iam.securityReviewer",
    "roles/cloudasset.viewer",
    "roles/logging.privateLogViewer",
    "roles/serviceusage.serviceUsageConsumer",
]

REQUIRED_APIS = [
    # Core
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "logging.googleapis.com",
    "cloudasset.googleapis.com",
    "policyanalyzer.googleapis.com",
    "recommender.googleapis.com",
    "serviceusage.googleapis.com",
    # WIF
    "sts.googleapis.com",
    "iamcredentials.googleapis.com",
    # Compute & Networking
    "compute.googleapis.com",
    # Serverless
    "run.googleapis.com",
    "cloudfunctions.googleapis.com",
    "eventarc.googleapis.com",
    "pubsub.googleapis.com",
    "apigateway.googleapis.com",
    # Data & Storage
    "bigquery.googleapis.com",
    "storage-api.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
]

# Fixed values
AWS_ACCOUNT_ID = "112665896816"
SA_NAME = "tamnoon-federate-svc-account"
POOL_ID = "tamnoon-pool-federate"
PROVIDER_ID = "tamnoon-aws-federate"
POOL_DISPLAY_NAME = "TamnoonWorkloadIdentityPool"

# WIF attribute mapping (same as main.tf)
ATTRIBUTE_MAPPING = (
    "google.subject=assertion.arn,"
    "attribute.aws_role="
    "assertion.arn.contains('assumed-role') "
    "? assertion.arn.extract('{account_arn}assumed-role/') + 'assumed-role/' + assertion.arn.extract('assumed-role/{role_name}/') "
    ": assertion.arn"
)


# =============================================================================
# Helper Functions
# =============================================================================

def run_gcloud(args_list, timeout=120):
    """Execute gcloud command and return (success, output, error)."""
    cmd = ["gcloud"] + args_list
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return True, result.stdout.strip(), None
        return False, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except FileNotFoundError:
        return False, "", "gcloud CLI not found. Please run this in Google Cloud Shell."
    except Exception as e:
        return False, "", str(e)


def check_gcloud_auth():
    """Verify gcloud is authenticated."""
    success, output, error = run_gcloud(["auth", "list", "--filter=status:ACTIVE", "--format=value(account)"])
    if success and output:
        return True, output.split('\n')[0]
    return False, error


def prompt_input(prompt_text, default=None):
    """Prompt user for input with optional default."""
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"{prompt_text}{suffix}: ").strip()
        return value if value else default
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        sys.exit(1)


def prompt_confirmation():
    """Prompt user for confirmation."""
    try:
        response = input("\nProceed? [y/N]: ").strip().lower()
        return response in ('y', 'yes')
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return False


def parse_resource_ids(input_str):
    """Parse comma or space separated resource IDs."""
    input_str = input_str.replace(",", " ")
    return [rid.strip() for rid in input_str.split() if rid.strip()]


def sa_email(identity_project):
    """Return the full SA email for the identity project."""
    return f"{SA_NAME}@{identity_project}.iam.gserviceaccount.com"


def get_project_number(identity_project):
    """Get the project number for a project ID."""
    success, number, error = run_gcloud([
        "projects", "describe", identity_project,
        "--format=value(projectNumber)",
    ])
    return number if success else None


# =============================================================================
# Validation
# =============================================================================

def validate_project_id(project_id):
    pattern = r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$'
    if re.match(pattern, project_id):
        return True, None
    return False, f"Invalid project ID: {project_id} (must be 6-30 chars, lowercase letters, digits, hyphens)"


def validate_org_id(org_id):
    if org_id.isdigit() and len(org_id) >= 1:
        return True, None
    return False, f"Invalid organization ID: {org_id} (must be numeric)"


def validate_folder_id(folder_id):
    if folder_id.isdigit() and len(folder_id) >= 1:
        return True, None
    return False, f"Invalid folder ID: {folder_id} (must be numeric)"


def validate_tenant_id(tenant_id):
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if re.match(pattern, tenant_id):
        return True, None
    return False, f"Invalid tenant ID: {tenant_id} (expected UUID format)"


def validate_resources(scope_type, resources):
    validators = {
        "organization": validate_org_id,
        "folder": validate_folder_id,
        "project": validate_project_id,
    }
    errors = []
    for resource_id in resources:
        valid, error = validators[scope_type](resource_id)
        if not valid:
            errors.append(error)
    return len(errors) == 0, errors


# =============================================================================
# Discovery
# =============================================================================

def check_sa_exists(identity_project):
    """Check if the Tamnoon SA exists. Returns True/False."""
    success, output, error = run_gcloud([
        "iam", "service-accounts", "describe", sa_email(identity_project),
        f"--project={identity_project}", "--format=value(email)",
    ])
    return success


def discover_current_scope(identity_project):
    """
    Discover where the Tamnoon SA currently has IAM bindings.
    Returns dict: {"organizations": [...], "folders": [...], "projects": [...]}
    """
    email = sa_email(identity_project)
    coverage = {"organizations": [], "folders": [], "projects": []}

    # Try Cloud Asset search first (requires cloudasset.assets.searchAllIamPolicies)
    success, output, error = run_gcloud([
        "asset", "search-all-iam-policies",
        f"--scope=projects/{identity_project}",
        f"--query=policy:{email}",
        "--format=json",
    ], timeout=180)

    if success and output:
        try:
            results = json.loads(output)
            for entry in results:
                resource = entry.get("resource", "")
                # Parse resource type from the full resource name
                if resource.startswith("//cloudresourcemanager.googleapis.com/organizations/"):
                    org_id = resource.split("/organizations/")[1]
                    if org_id not in coverage["organizations"]:
                        coverage["organizations"].append(org_id)
                elif resource.startswith("//cloudresourcemanager.googleapis.com/folders/"):
                    folder_id = resource.split("/folders/")[1]
                    if folder_id not in coverage["folders"]:
                        coverage["folders"].append(folder_id)
                elif resource.startswith("//cloudresourcemanager.googleapis.com/projects/"):
                    project_id = resource.split("/projects/")[1]
                    # Exclude the identity project's own SA IAM binding
                    if project_id not in coverage["projects"]:
                        coverage["projects"].append(project_id)
            return coverage
        except (json.JSONDecodeError, KeyError):
            pass

    # Fallback: try org-scoped search if project-scoped didn't return results
    # The operator might have org-level cloudasset access
    success, output, error = run_gcloud([
        "asset", "search-all-iam-policies",
        f"--query=policy:{email}",
        "--format=json",
    ], timeout=180)

    if success and output:
        try:
            results = json.loads(output)
            for entry in results:
                resource = entry.get("resource", "")
                if resource.startswith("//cloudresourcemanager.googleapis.com/organizations/"):
                    org_id = resource.split("/organizations/")[1]
                    if org_id not in coverage["organizations"]:
                        coverage["organizations"].append(org_id)
                elif resource.startswith("//cloudresourcemanager.googleapis.com/folders/"):
                    folder_id = resource.split("/folders/")[1]
                    if folder_id not in coverage["folders"]:
                        coverage["folders"].append(folder_id)
                elif resource.startswith("//cloudresourcemanager.googleapis.com/projects/"):
                    project_id = resource.split("/projects/")[1]
                    if project_id not in coverage["projects"]:
                        coverage["projects"].append(project_id)
        except (json.JSONDecodeError, KeyError):
            pass

    return coverage


def print_current_scope(coverage):
    """Display current scope coverage."""
    has_any = False

    if coverage["organizations"]:
        has_any = True
        for org_id in coverage["organizations"]:
            print(f"  Organization: {org_id}")

    if coverage["folders"]:
        has_any = True
        for folder_id in coverage["folders"]:
            print(f"  Folder:       {folder_id}")

    if coverage["projects"]:
        has_any = True
        for project_id in coverage["projects"]:
            print(f"  Project:      {project_id}")

    if not has_any:
        print("  No IAM bindings found (scope discovery may require cloudasset.assets.searchAllIamPolicies)")


# =============================================================================
# Step 1: Create Service Account
# =============================================================================

def create_service_account(identity_project):
    """Create the Tamnoon service account."""
    print(f"\n[Step 1/5] Creating service account {SA_NAME}...")

    email = sa_email(identity_project)

    # Check if already exists
    success, output, error = run_gcloud([
        "iam", "service-accounts", "describe", email,
        f"--project={identity_project}", "--format=value(email)",
    ])
    if success:
        print(f"  Service account already exists: {email}")
        return True, email

    success, output, error = run_gcloud([
        "iam", "service-accounts", "create", SA_NAME,
        f"--display-name={SA_NAME}",
        f"--project={identity_project}",
    ])
    if success:
        print(f"  \u2713 Created: {email}")
        return True, email

    print(f"  \u2717 Failed: {error}")
    return False, error


# =============================================================================
# Step 2: Create Workload Identity Pool
# =============================================================================

def create_wif_pool(identity_project):
    """Create the Workload Identity Federation pool."""
    print(f"\n[Step 2/5] Creating Workload Identity Pool {POOL_ID}...")

    success, output, error = run_gcloud([
        "iam", "workload-identity-pools", "describe", POOL_ID,
        "--location=global", f"--project={identity_project}",
        "--format=value(name)",
    ])
    if success:
        print(f"  Pool already exists: {POOL_ID}")
        return True

    success, output, error = run_gcloud([
        "iam", "workload-identity-pools", "create", POOL_ID,
        "--location=global",
        f"--display-name={POOL_DISPLAY_NAME}",
        f"--project={identity_project}",
    ])
    if success:
        print(f"  \u2713 Created: {POOL_ID}")
        return True

    print(f"  \u2717 Failed: {error}")
    return False


# =============================================================================
# Step 3: Create AWS Provider
# =============================================================================

def create_wif_provider(identity_project, tenant_id):
    """Create the AWS Workload Identity Provider."""
    print(f"\n[Step 3/5] Creating AWS provider {PROVIDER_ID}...")

    trusted_role = f"arn:aws:sts::{AWS_ACCOUNT_ID}:assumed-role/gcp-onboarding-trust-{tenant_id}"
    attribute_condition = f"attribute.aws_role == '{trusted_role}'"

    success, output, error = run_gcloud([
        "iam", "workload-identity-pools", "providers", "describe", PROVIDER_ID,
        f"--workload-identity-pool={POOL_ID}",
        "--location=global", f"--project={identity_project}",
        "--format=value(name)",
    ])
    if success:
        print(f"  Provider already exists: {PROVIDER_ID}")
        return True

    success, output, error = run_gcloud([
        "iam", "workload-identity-pools", "providers", "create-aws", PROVIDER_ID,
        f"--workload-identity-pool={POOL_ID}",
        "--location=global",
        f"--account-id={AWS_ACCOUNT_ID}",
        f"--display-name={PROVIDER_ID}",
        f"--attribute-mapping={ATTRIBUTE_MAPPING}",
        f"--attribute-condition={attribute_condition}",
        f"--project={identity_project}",
    ])
    if success:
        print(f"  \u2713 Created: {PROVIDER_ID}")
        return True

    print(f"  \u2717 Failed: {error}")
    return False


# =============================================================================
# Step 4: Bind WIF Principal to Service Account
# =============================================================================

def bind_wif_principal(identity_project, tenant_id):
    """Grant roles/iam.workloadIdentityUser to the trusted AWS role on the SA."""
    print(f"\n[Step 4/5] Binding WIF principal to service account...")

    project_number = get_project_number(identity_project)
    if not project_number:
        print(f"  \u2717 Failed to get project number")
        return False, None

    trusted_role = f"arn:aws:sts::{AWS_ACCOUNT_ID}:assumed-role/gcp-onboarding-trust-{tenant_id}"
    member = (
        f"principalSet://iam.googleapis.com/projects/{project_number}"
        f"/locations/global/workloadIdentityPools/{POOL_ID}"
        f"/attribute.aws_role/{trusted_role}"
    )

    print(f"  Principal: {member}")
    print(f"  Role:      roles/iam.workloadIdentityUser")
    print(f"  Target:    {sa_email(identity_project)}")

    success, output, error = run_gcloud([
        "iam", "service-accounts", "add-iam-policy-binding", sa_email(identity_project),
        "--role=roles/iam.workloadIdentityUser",
        f"--member={member}",
        f"--project={identity_project}",
    ])
    if success:
        print(f"  \u2713 Binding created")
        return True, project_number

    print(f"  \u2717 Failed: {error}")
    return False, project_number


# =============================================================================
# Step 5: Assign / Remove IAM Roles at Scope
# =============================================================================

def assign_roles(scope_type, resources, identity_project):
    """Assign the 6 predefined roles to the Tamnoon SA at the chosen scope."""
    member = f"serviceAccount:{sa_email(identity_project)}"
    total_resources = len(resources)

    print(f"\n[Step 5/5] Assigning {len(TAMNOON_ROLES)} roles to {total_resources} {scope_type}(s)...")

    results = {"success": 0, "failed": 0, "errors": []}

    for i, resource_id in enumerate(resources, 1):
        prefix = f"  [{i}/{total_resources}] " if total_resources > 1 else "  "
        print(f"{prefix}{scope_type} {resource_id}:")

        for role in TAMNOON_ROLES:
            if scope_type == "organization":
                cmd = ["organizations", "add-iam-policy-binding", resource_id,
                       f"--member={member}", f"--role={role}", "--quiet"]
            elif scope_type == "folder":
                cmd = ["resource-manager", "folders", "add-iam-policy-binding", resource_id,
                       f"--member={member}", f"--role={role}", "--quiet"]
            else:
                cmd = ["projects", "add-iam-policy-binding", resource_id,
                       f"--member={member}", f"--role={role}", "--quiet"]

            success, output, error = run_gcloud(cmd)
            if success:
                print(f"    \u2713 {role}")
                results["success"] += 1
            else:
                print(f"    \u2717 {role} ({error})")
                results["failed"] += 1
                results["errors"].append({"resource": resource_id, "role": role, "error": error})

    return results


def remove_roles(scope_type, resources, identity_project):
    """Remove the 6 predefined roles from the Tamnoon SA at the given scope."""
    member = f"serviceAccount:{sa_email(identity_project)}"
    total_resources = len(resources)

    print(f"\nRemoving {len(TAMNOON_ROLES)} roles from {total_resources} {scope_type}(s)...")

    results = {"success": 0, "failed": 0, "errors": []}

    for i, resource_id in enumerate(resources, 1):
        prefix = f"  [{i}/{total_resources}] " if total_resources > 1 else "  "
        print(f"{prefix}{scope_type} {resource_id}:")

        for role in TAMNOON_ROLES:
            if scope_type == "organization":
                cmd = ["organizations", "remove-iam-policy-binding", resource_id,
                       f"--member={member}", f"--role={role}", "--quiet"]
            elif scope_type == "folder":
                cmd = ["resource-manager", "folders", "remove-iam-policy-binding", resource_id,
                       f"--member={member}", f"--role={role}", "--quiet"]
            else:
                cmd = ["projects", "remove-iam-policy-binding", resource_id,
                       f"--member={member}", f"--role={role}", "--quiet"]

            success, output, error = run_gcloud(cmd)
            if success:
                print(f"    \u2713 {role} removed")
                results["success"] += 1
            else:
                print(f"    \u2717 {role} ({error})")
                results["failed"] += 1
                results["errors"].append({"resource": resource_id, "role": role, "error": error})

    return results


# =============================================================================
# API Enablement
# =============================================================================

def enable_apis(project_ids):
    """Enable required APIs on the given projects."""
    print(f"\nEnabling {len(REQUIRED_APIS)} APIs on {len(project_ids)} project(s)...")

    results = {"success": 0, "failed": 0}

    for i, project_id in enumerate(project_ids, 1):
        prefix = f"[{i}/{len(project_ids)}] " if len(project_ids) > 1 else ""
        print(f"\n{prefix}Project {project_id}:")

        for api in REQUIRED_APIS:
            success, output, error = run_gcloud([
                "services", "enable", api,
                f"--project={project_id}", "--quiet",
            ])
            if success:
                print(f"  \u2713 {api}")
                results["success"] += 1
            else:
                print(f"  \u2717 {api} ({error})")
                results["failed"] += 1

    return results


# =============================================================================
# Output
# =============================================================================

def print_onboarding_output(identity_project, project_number):
    """Print JSON output for Tamnoon onboarding completion."""
    success, sa_unique_id, error = run_gcloud([
        "iam", "service-accounts", "describe", sa_email(identity_project),
        f"--project={identity_project}",
        "--format=value(uniqueId)",
    ])
    if not success:
        sa_unique_id = "UNKNOWN"

    output = {
        "identity_project_number": project_number,
        "service_account_id": sa_unique_id,
        "workload_identity_pool_id": POOL_ID,
        "workload_identity_provider_id": PROVIDER_ID,
    }

    print("\n" + "=" * 64)
    print("ONBOARDING OUTPUT")
    print("Provide this JSON to Tamnoon to complete onboarding setup:")
    print("=" * 64)
    print(json.dumps(output, indent=2))
    print("=" * 64 + "\n")


# =============================================================================
# Operations
# =============================================================================

def do_fresh_onboarding(identity_project, tenant_id, scope_type, resources, do_enable_apis):
    """Execute fresh onboarding: create SA, WIF, bind, assign roles."""
    # Step 1: Create SA
    success, email = create_service_account(identity_project)
    if not success:
        print("\nAborting: service account creation failed.")
        return 1

    # Step 2: Create WIF pool
    if not create_wif_pool(identity_project):
        print("\nAborting: WIF pool creation failed.")
        return 1

    # Step 3: Create WIF provider
    if not create_wif_provider(identity_project, tenant_id):
        print("\nAborting: WIF provider creation failed.")
        return 1

    # Step 4: Bind WIF principal
    success, project_number = bind_wif_principal(identity_project, tenant_id)
    if not success:
        print("\nAborting: WIF principal binding failed.")
        return 1

    # Step 5: Assign roles
    results = assign_roles(scope_type, resources, identity_project)
    failed = results["failed"] > 0

    # API enablement
    if do_enable_apis:
        if scope_type == "project":
            api_projects = resources
        elif scope_type == "organization":
            print("\nDiscovering projects in organization for API enablement...")
            success, output, error = run_gcloud([
                "projects", "list", "--filter=lifecycleState:ACTIVE",
                "--format=value(projectId)",
            ])
            api_projects = [p for p in output.split('\n') if p.strip()] if success else []
        else:
            api_projects = []
            print("\nNote: API enablement for folder scope requires project discovery (not implemented).")

        if api_projects:
            api_results = enable_apis(api_projects)
            if api_results["failed"] > 0:
                failed = True

    # Summary
    print("\n" + "=" * 64)
    print("ONBOARDING SUMMARY")
    print(f"  Service account:  {email}")
    print(f"  WIF pool:         {POOL_ID}")
    print(f"  WIF provider:     {PROVIDER_ID}")
    print(f"  Roles assigned:   {results['success']}/{results['success'] + results['failed']}")
    if failed:
        print("\n  Some operations failed — review output above.")
    else:
        print("\n  All operations completed successfully.")
    print("=" * 64)

    print_onboarding_output(identity_project, project_number)
    return 1 if failed else 0


def do_expand_scope(identity_project, coverage, scope_type, resources):
    """Add IAM bindings for new resources."""
    # Cross-reference with current coverage
    current = set(coverage.get(f"{scope_type}s", []))
    requested = set(resources)
    already_covered = requested & current
    to_add = list(requested - current)

    if already_covered:
        print(f"\nSkipping (already covered):")
        for r in sorted(already_covered):
            print(f"  {r}")

    if not to_add:
        print("\nNothing to add — all requested resources are already covered.")
        return 0

    print(f"\nResources to add:")
    for r in to_add:
        print(f"  {r}")

    if not prompt_confirmation():
        print("Cancelled.")
        return 1

    results = assign_roles(scope_type, to_add, identity_project)

    print("\n" + "=" * 64)
    print("SCOPE EXPANSION SUMMARY")
    print(f"  Added:  {len(to_add)} {scope_type}(s)")
    print(f"  Roles:  {results['success']}/{results['success'] + results['failed']}")
    if results["failed"] > 0:
        print("  Some operations failed — review output above.")
    else:
        print("  All operations completed successfully.")
    print("=" * 64 + "\n")

    return 1 if results["failed"] > 0 else 0


def do_reduce_scope(identity_project, coverage, scope_type, resources):
    """Remove IAM bindings for specified resources."""
    current = set(coverage.get(f"{scope_type}s", []))
    requested = set(resources)
    not_found = requested - current
    to_remove = list(requested & current)

    if not_found:
        print(f"\nSkipping (no bindings found):")
        for r in sorted(not_found):
            print(f"  {r}")

    if not to_remove:
        print("\nNothing to remove — none of the requested resources have bindings.")
        return 0

    print(f"\nResources to remove:")
    for r in to_remove:
        print(f"  {r}")

    if not prompt_confirmation():
        print("Cancelled.")
        return 1

    results = remove_roles(scope_type, to_remove, identity_project)

    print("\n" + "=" * 64)
    print("SCOPE REDUCTION SUMMARY")
    print(f"  Removed: {len(to_remove)} {scope_type}(s)")
    print(f"  Roles:   {results['success']}/{results['success'] + results['failed']}")
    if results["failed"] > 0:
        print("  Some operations failed — review output above.")
    else:
        print("  All operations completed successfully.")
    print("=" * 64 + "\n")

    return 1 if results["failed"] > 0 else 0


def do_offboard(identity_project, coverage):
    """Remove all IAM bindings, delete WIF resources, delete SA."""
    print("\n" + "=" * 64)
    print("  WARNING: This will delete the Tamnoon service account,")
    print("  Workload Identity Pool, Provider, and all IAM bindings.")
    print("=" * 64)

    if not prompt_confirmation():
        print("Cancelled.")
        return 1

    failed = False

    # Step 1: Remove all discovered IAM bindings
    print("\n[Step 1/4] Removing IAM role bindings...")
    for scope_type_key, scope_cmd in [("organizations", "organization"), ("folders", "folder"), ("projects", "project")]:
        resources = coverage.get(scope_type_key, [])
        if resources:
            results = remove_roles(scope_cmd, resources, identity_project)
            if results["failed"] > 0:
                failed = True

    # Step 2: Delete WIF provider
    print(f"\n[Step 2/4] Deleting WIF provider {PROVIDER_ID}...")
    success, output, error = run_gcloud([
        "iam", "workload-identity-pools", "providers", "delete", PROVIDER_ID,
        f"--workload-identity-pool={POOL_ID}",
        "--location=global", f"--project={identity_project}", "--quiet",
    ])
    if success:
        print(f"  \u2713 Deleted: {PROVIDER_ID}")
    else:
        print(f"  \u2717 Failed: {error}")
        failed = True

    # Step 3: Delete WIF pool
    print(f"\n[Step 3/4] Deleting WIF pool {POOL_ID}...")
    success, output, error = run_gcloud([
        "iam", "workload-identity-pools", "delete", POOL_ID,
        "--location=global", f"--project={identity_project}", "--quiet",
    ])
    if success:
        print(f"  \u2713 Deleted: {POOL_ID}")
    else:
        print(f"  \u2717 Failed: {error}")
        failed = True

    # Step 4: Delete SA
    print(f"\n[Step 4/4] Deleting service account {SA_NAME}...")
    success, output, error = run_gcloud([
        "iam", "service-accounts", "delete", sa_email(identity_project),
        f"--project={identity_project}", "--quiet",
    ])
    if success:
        print(f"  \u2713 Deleted: {sa_email(identity_project)}")
    else:
        print(f"  \u2717 Failed: {error}")
        failed = True

    print("\n" + "=" * 64)
    print("OFFBOARDING SUMMARY")
    if failed:
        print("  Some operations failed — review output above.")
    else:
        print("  Tamnoon onboarding fully removed.")
    print("=" * 64 + "\n")

    return 1 if failed else 0


# =============================================================================
# Plan Display
# =============================================================================

def show_fresh_plan(identity_project, tenant_id, scope_type, resources, do_enable_apis):
    """Display planned actions for fresh onboarding."""
    trusted_role = f"gcp-onboarding-trust-{tenant_id}"

    print(f"\nIdentity project:    {identity_project}")
    print(f"Tamnoon tenant ID:   {tenant_id}")
    print(f"Scope:               {scope_type.capitalize()}")

    if len(resources) == 1:
        print(f"Target:              {resources[0]}")
    else:
        print(f"Targets:             {', '.join(resources)}")

    print(f"\nResources to create:")
    print(f"  1. Service account:  {sa_email(identity_project)}")
    print(f"  2. WIF pool:         {POOL_ID}")
    print(f"  3. WIF provider:     {PROVIDER_ID} (AWS {AWS_ACCOUNT_ID})")
    print(f"  4. WIF binding:      roles/iam.workloadIdentityUser")
    print(f"     Trusted role:     {trusted_role}")

    print(f"\nRoles to assign ({len(TAMNOON_ROLES)}):")
    for role in TAMNOON_ROLES:
        print(f"  - {role}")

    if do_enable_apis:
        print(f"\nAPI enablement:      Yes ({len(REQUIRED_APIS)} APIs)")


# =============================================================================
# Interactive Prompts
# =============================================================================

def prompt_identity_project():
    """Prompt for identity project with explanation."""
    print("\nIdentity Project")
    print("  The GCP project where the Tamnoon service account, Workload Identity")
    print("  Pool, and Provider will be created. This can be any project in your")
    print("  organization (e.g., a shared infrastructure or security project).")
    identity_project = prompt_input("\nEnter project ID")
    if not identity_project:
        print("Project ID is required.")
        sys.exit(1)
    valid, error = validate_project_id(identity_project)
    if not valid:
        print(error)
        sys.exit(1)
    return identity_project


def prompt_tenant_id():
    """Prompt for Tamnoon tenant ID with explanation."""
    print("\nTamnoon Tenant ID")
    print("  Your Tamnoon tenant identifier (UUID format). This is provided by")
    print("  Tamnoon during onboarding and is used to establish the trust")
    print("  relationship between Tamnoon's AWS environment and your GCP project.")
    tenant_id = prompt_input("\nEnter tenant ID")
    if not tenant_id:
        print("Tenant ID is required.")
        sys.exit(1)
    valid, error = validate_tenant_id(tenant_id)
    if not valid:
        print(error)
        sys.exit(1)
    return tenant_id


def prompt_scope():
    """Prompt for onboarding scope with explanation."""
    print("\nOnboarding Scope")
    print("  Determines where the Tamnoon service account will receive IAM roles.")
    print("  Organization scope is recommended — it covers all current and future")
    print("  projects through IAM inheritance. Folder or project scope limits")
    print("  access to specific parts of your hierarchy.")
    print()
    print("  1. Organization (recommended — covers all projects)")
    print("  2. Folder (covers all projects within selected folders)")
    print("  3. Project (covers only the selected projects)")

    scope_choice = prompt_input("\nEnter choice [1-3]")
    scope_map = {"1": "organization", "2": "folder", "3": "project"}
    if scope_choice not in scope_map:
        print("Invalid choice.")
        sys.exit(1)
    return scope_map[scope_choice]


def prompt_scope_resources(scope_type):
    """Prompt for scope resource IDs with explanation."""
    if scope_type == "organization":
        print("\nOrganization ID")
        print("  The numeric ID of your GCP organization. You can find it in the")
        print("  GCP Console under IAM & Admin > Settings, or by running:")
        print("  gcloud organizations list")
        resource_input = prompt_input("\nEnter organization ID")
    elif scope_type == "folder":
        print("\nFolder ID(s)")
        print("  The numeric ID(s) of the GCP folder(s) to onboard. All projects")
        print("  within these folders will be covered through IAM inheritance.")
        print("  For multiple folders, separate with commas or spaces.")
        resource_input = prompt_input("\nEnter folder ID(s)")
    else:
        print("\nProject ID(s)")
        print("  The GCP project ID(s) to onboard. Only these specific projects")
        print("  will be covered. For multiple projects, separate with commas or spaces.")
        resource_input = prompt_input("\nEnter project ID(s)")

    if not resource_input:
        print("No resource IDs provided.")
        sys.exit(1)

    resources = parse_resource_ids(resource_input)
    if scope_type == "organization" and len(resources) > 1:
        print("Organization scope supports a single ID.")
        resources = [resources[0]]

    valid, errors = validate_resources(scope_type, resources)
    if not valid:
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    return resources


def prompt_enable_apis():
    """Prompt for API enablement with explanation."""
    print("\nAPI Enablement")
    print("  Tamnoon requires specific GCP APIs to be enabled on each project in")
    print(f"  scope ({len(REQUIRED_APIS)} APIs including IAM, Cloud Asset, Logging, Compute, etc.).")
    print("  This step is safe to run — API enablement is idempotent.")
    choice = prompt_input("\nEnable required APIs on target projects? [y/N]", "N")
    return choice.lower() in ('y', 'yes')


# =============================================================================
# Interactive Mode
# =============================================================================

def interactive_mode():
    """Run in interactive mode with prompts."""
    print("\n" + "=" * 64)
    print("         Tamnoon GCP Onboarding — Interactive Setup")
    print("=" * 64)

    # Check auth
    auth_ok, account = check_gcloud_auth()
    if not auth_ok:
        print(f"\nError: Not authenticated. {account}")
        print("Please run 'gcloud auth login' first.")
        return 1
    print(f"\nAuthenticated as: {account}")

    # Identity project
    identity_project = prompt_identity_project()

    # Check if SA already exists
    sa_exists = check_sa_exists(identity_project)

    if not sa_exists:
        # Fresh onboarding
        print(f"\nNo existing Tamnoon service account found in {identity_project}.")
        print("Proceeding with fresh onboarding.\n")

        tenant_id = prompt_tenant_id()
        scope_type = prompt_scope()
        resources = prompt_scope_resources(scope_type)
        do_enable_apis = prompt_enable_apis()

        print("\n" + "=" * 64)
        print("         Tamnoon GCP Onboarding — Execution Plan")
        print("=" * 64)
        show_fresh_plan(identity_project, tenant_id, scope_type, resources, do_enable_apis)

        if not prompt_confirmation():
            print("Cancelled.")
            return 1

        return do_fresh_onboarding(identity_project, tenant_id, scope_type, resources, do_enable_apis)

    # SA exists — discover current scope
    print(f"\nExisting Tamnoon onboarding detected:")
    print(f"  Service account:  {sa_email(identity_project)}")
    print(f"  WIF pool:         {POOL_ID}")
    print(f"  WIF provider:     {PROVIDER_ID}")

    print(f"\nDiscovering current scope coverage...")
    coverage = discover_current_scope(identity_project)

    print(f"\nCurrent scope:")
    print_current_scope(coverage)

    # Menu
    print("\nWhat would you like to do?")
    print("  1. Expand scope (add projects, folders, or organization)")
    print("  2. Reduce scope (remove projects, folders, or organization)")
    print("  3. Offboarding (delete Tamnoon SA and associated WIF Pool and Provider)")

    choice = prompt_input("\nEnter choice [1-3]")

    if choice == "1":
        scope_type = prompt_scope()
        resources = prompt_scope_resources(scope_type)
        return do_expand_scope(identity_project, coverage, scope_type, resources)

    elif choice == "2":
        scope_type = prompt_scope()
        resources = prompt_scope_resources(scope_type)
        return do_reduce_scope(identity_project, coverage, scope_type, resources)

    elif choice == "3":
        return do_offboard(identity_project, coverage)

    else:
        print("Invalid choice.")
        return 1


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Tamnoon GCP Onboarding — Create service account with WIF and assign permissions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python3 tamnoon_onboarding.py

  # Fresh onboarding — organization scope
  python3 tamnoon_onboarding.py \\
      --identity-project my-infra-project \\
      --tenant-id 5104b7b7-56ee-4f51-97d8-0a6c49f846f5 \\
      --scope organization --org-id 123456789

  # Fresh onboarding — project scope with API enablement
  python3 tamnoon_onboarding.py \\
      --identity-project my-infra-project \\
      --tenant-id 5104b7b7-56ee-4f51-97d8-0a6c49f846f5 \\
      --scope project --project-ids proj-a proj-b \\
      --enable-apis -y

  # Expand scope
  python3 tamnoon_onboarding.py \\
      --identity-project my-infra-project \\
      --expand --scope project --project-ids new-proj-a new-proj-b

  # Reduce scope
  python3 tamnoon_onboarding.py \\
      --identity-project my-infra-project \\
      --reduce --scope project --project-ids old-proj-a

  # Offboard
  python3 tamnoon_onboarding.py \\
      --identity-project my-infra-project --offboard
        """
    )

    parser.add_argument("--identity-project", metavar="PROJECT_ID",
                        help="GCP project ID where the SA and WIF resources are created")
    parser.add_argument("--tenant-id", metavar="UUID",
                        help="Tamnoon tenant ID (required for fresh onboarding)")
    parser.add_argument("--scope", choices=["organization", "folder", "project"],
                        help="Scope level for IAM role assignment")
    parser.add_argument("--org-id", metavar="ORG_ID",
                        help="Organization ID (for organization scope)")
    parser.add_argument("--folder-ids", nargs="+", metavar="ID",
                        help="One or more folder IDs (for folder scope)")
    parser.add_argument("--project-ids", nargs="+", metavar="ID",
                        help="One or more project IDs (for project scope)")
    parser.add_argument("--expand", action="store_true",
                        help="Expand scope — add resources to existing onboarding")
    parser.add_argument("--reduce", action="store_true",
                        help="Reduce scope — remove resources from existing onboarding")
    parser.add_argument("--offboard", action="store_true",
                        help="Delete Tamnoon SA, WIF Pool, Provider, and all IAM bindings")
    parser.add_argument("--enable-apis", action="store_true",
                        help="Enable required GCP APIs on target projects")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Skip confirmation prompt")

    args = parser.parse_args()

    # Interactive mode if no identity-project
    if not args.identity_project:
        return interactive_mode()

    # Validate identity project
    valid, error = validate_project_id(args.identity_project)
    if not valid:
        parser.error(error)

    # Check auth
    auth_ok, account = check_gcloud_auth()
    if not auth_ok:
        print(f"Error: Not authenticated. {account}")
        return 1

    # Offboard mode
    if args.offboard:
        print(f"\nDiscovering current scope for {args.identity_project}...")
        coverage = discover_current_scope(args.identity_project)
        print("\nCurrent scope:")
        print_current_scope(coverage)
        if not args.yes:
            if not prompt_confirmation():
                print("Cancelled.")
                return 1
        return do_offboard(args.identity_project, coverage)

    # Expand / Reduce modes
    if args.expand or args.reduce:
        if not args.scope:
            parser.error("--scope is required with --expand or --reduce")

        resources = _resolve_scope_resources(parser, args)
        valid, errors = validate_resources(args.scope, resources)
        if not valid:
            for e in errors:
                print(f"  - {e}")
            return 1

        coverage = discover_current_scope(args.identity_project)
        print(f"\nCurrent scope:")
        print_current_scope(coverage)

        if args.expand:
            return do_expand_scope(args.identity_project, coverage, args.scope, resources)
        else:
            return do_reduce_scope(args.identity_project, coverage, args.scope, resources)

    # Fresh onboarding
    if not args.tenant_id:
        parser.error("--tenant-id is required for fresh onboarding")
    if not args.scope:
        parser.error("--scope is required for fresh onboarding")

    valid, error = validate_tenant_id(args.tenant_id)
    if not valid:
        parser.error(error)

    resources = _resolve_scope_resources(parser, args)
    valid, errors = validate_resources(args.scope, resources)
    if not valid:
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\n" + "=" * 64)
    print("         Tamnoon GCP Onboarding — Execution Plan")
    print("=" * 64)
    show_fresh_plan(args.identity_project, args.tenant_id, args.scope, resources, args.enable_apis)

    if not args.yes:
        if not prompt_confirmation():
            print("Cancelled.")
            return 1

    return do_fresh_onboarding(args.identity_project, args.tenant_id, args.scope, resources, args.enable_apis)


def _resolve_scope_resources(parser, args):
    """Extract resource list from CLI args based on scope."""
    if args.scope == "organization":
        if not args.org_id:
            parser.error("--org-id is required for organization scope")
        return [args.org_id]
    elif args.scope == "folder":
        if not args.folder_ids:
            parser.error("--folder-ids is required for folder scope")
        return args.folder_ids
    elif args.scope == "project":
        if not args.project_ids:
            parser.error("--project-ids is required for project scope")
        return args.project_ids


if __name__ == "__main__":
    sys.exit(main())
