#!/usr/bin/env python3
"""
Tamnoon GCP Onboarding - Permission Assignment Script

Run in Google Cloud Shell to assign required Tamnoon permissions.

Usage:
    python3 tamnoon_onboarding.py                              # Interactive mode
    python3 tamnoon_onboarding.py --help                       # Show help
    python3 tamnoon_onboarding.py --scope organization --org-id 123456789
    python3 tamnoon_onboarding.py --scope folder --folder-ids 111 222 333
    python3 tamnoon_onboarding.py --scope project --project-ids proj-a proj-b -y
    python3 tamnoon_onboarding.py --scope project --project-ids proj-a --enable-apis
    python3 tamnoon_onboarding.py --scope organization --org-id 123456789 --member team@company.com --member-type group
"""

import argparse
import json
import re
import subprocess
import sys

# =============================================================================
# Role Definitions by Scope
# =============================================================================

ORG_ROLES = [
    "roles/viewer",
    "roles/browser",
    "roles/iam.securityReviewer",
    "roles/cloudasset.viewer",
    "roles/logging.privateLogViewer",
    "roles/serviceusage.serviceUsageConsumer",
]

FOLDER_ROLES = [
    "roles/viewer",
    "roles/browser",
    "roles/iam.securityReviewer",
    "roles/cloudasset.viewer",
    "roles/logging.privateLogViewer",
    "roles/serviceusage.serviceUsageConsumer",
]

PROJECT_ROLES = [
    "roles/viewer",
    "roles/browser",
    "roles/iam.securityReviewer",
    "roles/cloudasset.viewer",
    "roles/logging.privateLogViewer",
    "roles/serviceusage.serviceUsageConsumer",
]

# =============================================================================
# Required APIs (enabled per-project)
# =============================================================================

REQUIRED_APIS = [
    # Core
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "logging.googleapis.com",
    "cloudasset.googleapis.com",
    "policyanalyzer.googleapis.com",
    "recommender.googleapis.com",
    "serviceusage.googleapis.com",
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

DEFAULT_MEMBER = "tamnoonpoc@tamnoon.io"

# =============================================================================
# Helper Functions
# =============================================================================

def run_gcloud(args_list, timeout=60):
    """Execute gcloud command and return (success, output, error)."""
    cmd = ["gcloud"] + args_list
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
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


def parse_resource_ids(input_str):
    """Parse comma or space separated resource IDs."""
    input_str = input_str.replace(",", " ")
    return [rid.strip() for rid in input_str.split() if rid.strip()]


def format_member(email, member_type):
    """Format member string for gcloud command."""
    return f"{member_type}:{email}"


# =============================================================================
# Input Validation Functions
# =============================================================================

def validate_email(email):
    """Validate email format. Returns (is_valid, error_message)."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, None
    return False, f"Invalid email format: {email}"


def validate_org_id(org_id):
    """Validate organization ID (numeric). Returns (is_valid, error_message)."""
    if org_id.isdigit() and len(org_id) >= 1:
        return True, None
    return False, f"Invalid organization ID: {org_id} (must be numeric)"


def validate_folder_id(folder_id):
    """Validate folder ID (numeric). Returns (is_valid, error_message)."""
    if folder_id.isdigit() and len(folder_id) >= 1:
        return True, None
    return False, f"Invalid folder ID: {folder_id} (must be numeric)"


def validate_project_id(project_id):
    """Validate project ID format. Returns (is_valid, error_message)."""
    pattern = r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$'
    if re.match(pattern, project_id):
        return True, None
    return False, f"Invalid project ID: {project_id} (must be 6-30 chars, lowercase letters, digits, hyphens)"


def validate_resources(scope_type, resources):
    """Validate all resource IDs for the given scope. Returns (is_valid, errors)."""
    errors = []

    for resource_id in resources:
        if scope_type == "organization":
            valid, error = validate_org_id(resource_id)
        elif scope_type == "folder":
            valid, error = validate_folder_id(resource_id)
        elif scope_type == "project":
            valid, error = validate_project_id(resource_id)
        else:
            valid, error = False, f"Unknown scope type: {scope_type}"

        if not valid:
            errors.append(error)

    return len(errors) == 0, errors


# =============================================================================
# Project Discovery Functions
# =============================================================================

def discover_projects_in_org(org_id):
    """List all active projects in the organization."""
    print(f"\nDiscovering projects in organization {org_id}...")
    success, output, error = run_gcloud([
        "projects", "list",
        "--filter=lifecycleState:ACTIVE",
        "--format=value(projectId)",
    ], timeout=120)

    if not success:
        print(f"  Failed to list projects: {error}")
        return []

    projects = [p for p in output.split('\n') if p.strip()]
    print(f"  Found {len(projects)} active project(s)")
    return projects


def discover_projects_in_folders(folder_ids):
    """Recursively list all active projects under folder(s)."""
    all_projects = []
    visited_folders = set()

    def _recurse(folder_id):
        if folder_id in visited_folders:
            return
        visited_folders.add(folder_id)

        # Direct child projects
        success, output, error = run_gcloud([
            "projects", "list",
            f"--filter=parent.id={folder_id} AND lifecycleState:ACTIVE",
            "--format=value(projectId)",
        ], timeout=120)

        if success and output:
            projects = [p for p in output.split('\n') if p.strip()]
            all_projects.extend(projects)

        # Child folders — recurse
        success, output, error = run_gcloud([
            "resource-manager", "folders", "list",
            f"--folder={folder_id}",
            "--format=value(name)",
        ], timeout=60)

        if success and output:
            for child in output.split('\n'):
                child = child.strip()
                if child:
                    child_id = child.replace("folders/", "")
                    _recurse(child_id)

    print(f"\nDiscovering projects in {len(folder_ids)} folder(s)...")
    for folder_id in folder_ids:
        _recurse(folder_id)

    # Deduplicate (a project could appear via multiple paths)
    all_projects = list(dict.fromkeys(all_projects))
    print(f"  Found {len(all_projects)} active project(s)")
    return all_projects


# =============================================================================
# API Enablement Functions
# =============================================================================

def enable_apis_on_project(project_id, apis, project_index=None, total_projects=None):
    """Enable APIs on a single project. Returns results dict."""
    results = {"success": 0, "failed": 0, "errors": []}

    prefix = ""
    if project_index is not None and total_projects is not None:
        prefix = f"[{project_index}/{total_projects}] "

    print(f"\n{prefix}Enabling APIs on project {project_id}...")

    for api in apis:
        # gcloud services enable is idempotent — safe to re-run
        success, output, error = run_gcloud([
            "services", "enable", api,
            f"--project={project_id}",
            "--quiet",
        ], timeout=120)

        if success:
            print(f"  \u2713 {api}")
            results["success"] += 1
        else:
            print(f"  \u2717 {api} ({error})")
            results["failed"] += 1
            results["errors"].append({"api": api, "error": error})

    return results


def run_enable_apis(scope_type, resources, auto_approve=False):
    """Discover projects and enable APIs. Returns exit code."""
    # Discover projects based on scope
    if scope_type == "project":
        projects = resources
    elif scope_type == "organization":
        projects = discover_projects_in_org(resources[0])
    elif scope_type == "folder":
        projects = discover_projects_in_folders(resources)
    else:
        print(f"Unknown scope: {scope_type}")
        return 1

    if not projects:
        print("No projects found. Cannot enable APIs.")
        return 1

    # Show plan
    print(f"\nAPIs to enable ({len(REQUIRED_APIS)}):")
    for api in REQUIRED_APIS:
        print(f"  - {api}")

    print(f"\nTarget projects ({len(projects)}):")
    for project_id in projects:
        print(f"  - {project_id}")

    print(f"\nTotal operations: {len(REQUIRED_APIS)} APIs x {len(projects)} projects = {len(REQUIRED_APIS) * len(projects)}")

    if not auto_approve:
        if not prompt_confirmation():
            print("Cancelled.")
            return 1

    # Enable APIs on each project
    results_by_project = {}
    total = len(projects)

    for i, project_id in enumerate(projects, 1):
        index = i if total > 1 else None
        total_count = total if total > 1 else None
        results = enable_apis_on_project(project_id, REQUIRED_APIS, index, total_count)
        results_by_project[project_id] = results

    # Summary
    print("\n" + "=" * 64)
    print("API ENABLEMENT SUMMARY")

    total_success = sum(r["success"] for r in results_by_project.values())
    total_failed = sum(r["failed"] for r in results_by_project.values())
    total_ops = total_success + total_failed

    if len(projects) == 1:
        project_id = projects[0]
        result = results_by_project[project_id]
        if result["failed"] == 0:
            print(f"SUCCESS: {result['success']}/{result['success'] + result['failed']} APIs enabled on {project_id}")
        else:
            print(f"PARTIAL: {result['success']}/{result['success'] + result['failed']} APIs enabled on {project_id} ({result['failed']} failed)")
            for err in result["errors"]:
                print(f"  {err['api']}: {err['error']}")
    else:
        print(f"{len(projects)} projects processed: {total_success}/{total_ops} API enablements succeeded")
        for project_id, result in results_by_project.items():
            if result["failed"] == 0:
                print(f"  {project_id}: {result['success']}/{result['success'] + result['failed']} \u2713")
            else:
                print(f"  {project_id}: {result['success']}/{result['success'] + result['failed']} ({result['failed']} failed)")

    print("=" * 64 + "\n")

    return 1 if total_failed > 0 else 0


# =============================================================================
# Role Assignment Functions
# =============================================================================

def assign_role(scope_type, resource_id, member, role):
    """Assign a single role and return (success, error_message)."""
    if scope_type == "organization":
        cmd = ["organizations", "add-iam-policy-binding", resource_id,
               f"--member={member}", f"--role={role}", "--quiet"]
    elif scope_type == "folder":
        cmd = ["resource-manager", "folders", "add-iam-policy-binding", resource_id,
               f"--member={member}", f"--role={role}", "--quiet"]
    elif scope_type == "project":
        cmd = ["projects", "add-iam-policy-binding", resource_id,
               f"--member={member}", f"--role={role}", "--quiet"]
    else:
        return False, f"Unknown scope type: {scope_type}"

    success, output, error = run_gcloud(cmd)
    if success:
        return True, None
    return False, error or "Unknown error"


def assign_roles_to_resource(scope_type, resource_id, member, roles, resource_index=None, total_resources=None):
    """Assign all roles to a single resource."""
    results = {"success": 0, "failed": 0, "errors": []}

    prefix = ""
    if resource_index is not None and total_resources is not None:
        prefix = f"[{resource_index}/{total_resources}] "

    print(f"\n{prefix}Assigning roles to {scope_type} {resource_id}...")

    for role in roles:
        success, error = assign_role(scope_type, resource_id, member, role)
        if success:
            print(f"  \u2713 {role}")
            results["success"] += 1
        else:
            print(f"  \u2717 {role} ({error})")
            results["failed"] += 1
            results["errors"].append({"role": role, "error": error})

    return results


# =============================================================================
# Validation and Display Functions
# =============================================================================

def print_header():
    """Print script header."""
    print("\n" + "=" * 64)
    print("         Tamnoon GCP Onboarding - Permission Setup")
    print("=" * 64)


def show_validation_summary(scope_type, resources, member, roles, enable_apis=False):
    """Display planned actions."""
    print_header()
    print(f"\nScope:       {scope_type.capitalize()}")

    if len(resources) == 1:
        print(f"Resource:    {resources[0]}")
    else:
        print(f"Resources:   {', '.join(resources)}")

    print(f"Member:      {member}")

    if len(resources) > 1:
        print(f"\nRoles to assign per {scope_type}:")
    else:
        print("\nRoles to assign:")

    for role in roles:
        print(f"  - {role}")

    if enable_apis:
        print(f"\nAPI enablement: Yes ({len(REQUIRED_APIS)} APIs per project)")

    return True


def prompt_confirmation():
    """Prompt user for confirmation."""
    try:
        response = input("\nProceed? [y/N]: ").strip().lower()
        return response in ('y', 'yes')
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return False


def print_summary(scope_type, results_by_resource):
    """Print final summary."""
    print("\n" + "=" * 64)
    print("ROLE ASSIGNMENT SUMMARY")

    total_resources = len(results_by_resource)

    if total_resources == 1:
        resource_id = list(results_by_resource.keys())[0]
        result = results_by_resource[resource_id]
        total = result["success"] + result["failed"]
        if result["failed"] == 0:
            print(f"SUCCESS: {result['success']}/{total} roles assigned")
        else:
            print(f"PARTIAL: {result['success']}/{total} roles assigned ({result['failed']} failed)")
    else:
        print(f"SUMMARY: {total_resources} resources processed")
        for resource_id, result in results_by_resource.items():
            total = result["success"] + result["failed"]
            if result["failed"] == 0:
                print(f"  {resource_id}: {result['success']}/{total} roles \u2713")
            else:
                print(f"  {resource_id}: {result['success']}/{total} roles ({result['failed']} failed)")

    print("=" * 64 + "\n")


def print_enable_apis_hint(scope_type, resources):
    """Print hint about enabling APIs."""
    print("To enable required GCP APIs on projects in scope, re-run with --enable-apis:")
    if scope_type == "organization":
        print(f"  python3 tamnoon_onboarding.py --scope organization --org-id {resources[0]} --enable-apis")
    elif scope_type == "folder":
        ids = " ".join(resources)
        print(f"  python3 tamnoon_onboarding.py --scope folder --folder-ids {ids} --enable-apis")
    elif scope_type == "project":
        ids = " ".join(resources)
        print(f"  python3 tamnoon_onboarding.py --scope project --project-ids {ids} --enable-apis")
    print()


# =============================================================================
# Interactive Mode
# =============================================================================

def interactive_mode():
    """Run in interactive mode with prompts."""
    print_header()

    # Check authentication
    auth_ok, account = check_gcloud_auth()
    if not auth_ok:
        print(f"\nError: Not authenticated with gcloud. {account}")
        print("Please run 'gcloud auth login' first.")
        return 1

    print(f"\nAuthenticated as: {account}")

    # 1. Select scope
    print("\nSelect scope:")
    print("  1. Organization (recommended)")
    print("  2. Folder")
    print("  3. Project")

    try:
        scope_choice = input("\nEnter choice [1-3]: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 1

    scope_map = {"1": "organization", "2": "folder", "3": "project"}
    if scope_choice not in scope_map:
        print("Invalid choice.")
        return 1

    scope_type = scope_map[scope_choice]

    # 2. Get resource ID(s)
    if scope_type == "organization":
        prompt = "\nEnter organization ID: "
        roles = ORG_ROLES
    elif scope_type == "folder":
        prompt = "\nEnter folder ID(s) (comma or space separated): "
        roles = FOLDER_ROLES
    else:
        prompt = "\nEnter project ID(s) (comma or space separated): "
        roles = PROJECT_ROLES

    try:
        resource_input = input(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 1

    if not resource_input:
        print("No resource IDs provided.")
        return 1

    resources = parse_resource_ids(resource_input)
    if not resources:
        print("No valid resource IDs provided.")
        return 1

    if scope_type == "organization" and len(resources) > 1:
        print("Organization scope only supports a single organization ID.")
        resources = [resources[0]]

    # Validate resource IDs
    valid, errors = validate_resources(scope_type, resources)
    if not valid:
        print("\nValidation errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    # 3. Get member email
    try:
        member_input = input(f"\nEnter member email [{DEFAULT_MEMBER}]: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 1

    member_email = member_input if member_input else DEFAULT_MEMBER

    valid, error = validate_email(member_email)
    if not valid:
        print(f"\n{error}")
        return 1

    # 4. Get member type
    try:
        type_input = input("Member type - (u)ser, (s)erviceAccount, or (g)roup [u]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 1

    if type_input in ('s', 'serviceaccount'):
        member_type = "serviceAccount"
    elif type_input in ('g', 'group'):
        member_type = "group"
    else:
        member_type = "user"
    member = format_member(member_email, member_type)

    # 5. Show validation and confirm
    show_validation_summary(scope_type, resources, member, roles)

    if not prompt_confirmation():
        print("Cancelled.")
        return 1

    # 6. Execute role assignment
    results_by_resource = {}
    total = len(resources)

    for i, resource_id in enumerate(resources, 1):
        index = i if total > 1 else None
        total_count = total if total > 1 else None
        results = assign_roles_to_resource(scope_type, resource_id, member, roles, index, total_count)
        results_by_resource[resource_id] = results

    print_summary(scope_type, results_by_resource)

    # 7. Hint about API enablement
    print_enable_apis_hint(scope_type, resources)

    if any(r["failed"] > 0 for r in results_by_resource.values()):
        return 1
    return 0


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Tamnoon GCP Onboarding - Assign required permissions and enable APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tamnoon_onboarding.py
  python3 tamnoon_onboarding.py --scope organization --org-id 123456789
  python3 tamnoon_onboarding.py --scope folder --folder-ids 111 222 333
  python3 tamnoon_onboarding.py --scope project --project-ids proj-a proj-b -y
  python3 tamnoon_onboarding.py --scope project --project-ids proj-a --enable-apis
  python3 tamnoon_onboarding.py --scope organization --org-id 123456789 --enable-apis -y
        """
    )

    parser.add_argument("--scope", choices=["organization", "folder", "project"],
                        help="Scope level for permission assignment")
    parser.add_argument("--org-id", metavar="ORG_ID",
                        help="Organization ID (for organization scope)")
    parser.add_argument("--folder-ids", nargs="+", metavar="ID",
                        help="One or more folder IDs (for folder scope)")
    parser.add_argument("--project-ids", nargs="+", metavar="ID",
                        help="One or more project IDs (for project scope)")
    parser.add_argument("--member", default=DEFAULT_MEMBER,
                        help=f"Member email (default: {DEFAULT_MEMBER})")
    parser.add_argument("--member-type", choices=["user", "serviceAccount", "group"], default="user",
                        help="Member type: user, serviceAccount, or group (default: user)")
    parser.add_argument("--enable-apis", action="store_true",
                        help="Enable required GCP APIs on projects in scope")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Skip confirmation prompt (auto-approve)")

    args = parser.parse_args()

    # If no scope provided, run interactive mode
    if not args.scope:
        return interactive_mode()

    # CLI mode - validate arguments
    if args.scope == "organization":
        if not args.org_id:
            parser.error("--org-id is required for organization scope")
        resources = [args.org_id]
        roles = ORG_ROLES
    elif args.scope == "folder":
        if not args.folder_ids:
            parser.error("--folder-ids is required for folder scope")
        resources = args.folder_ids
        roles = FOLDER_ROLES
    elif args.scope == "project":
        if not args.project_ids:
            parser.error("--project-ids is required for project scope")
        resources = args.project_ids
        roles = PROJECT_ROLES

    # Validate resource IDs
    valid, errors = validate_resources(args.scope, resources)
    if not valid:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    # Validate email
    valid, error = validate_email(args.member)
    if not valid:
        print(error)
        return 1

    member = format_member(args.member, args.member_type)

    # Check authentication
    auth_ok, account = check_gcloud_auth()
    if not auth_ok:
        print(f"Error: Not authenticated with gcloud. {account}")
        print("Please run 'gcloud auth login' first.")
        return 1

    # Show validation summary
    show_validation_summary(args.scope, resources, member, roles, enable_apis=args.enable_apis)

    # Confirm unless --yes
    if not args.yes:
        if not prompt_confirmation():
            print("Cancelled.")
            return 1

    # Execute role assignment
    results_by_resource = {}
    total = len(resources)

    for i, resource_id in enumerate(resources, 1):
        index = i if total > 1 else None
        total_count = total if total > 1 else None
        results = assign_roles_to_resource(args.scope, resource_id, member, roles, index, total_count)
        results_by_resource[resource_id] = results

    print_summary(args.scope, results_by_resource)

    role_failed = any(r["failed"] > 0 for r in results_by_resource.values())

    # Execute API enablement if requested
    if args.enable_apis:
        api_exit = run_enable_apis(args.scope, resources, auto_approve=args.yes)
        return 1 if (role_failed or api_exit != 0) else 0
    else:
        print_enable_apis_hint(args.scope, resources)
        return 1 if role_failed else 0


if __name__ == "__main__":
    sys.exit(main())
