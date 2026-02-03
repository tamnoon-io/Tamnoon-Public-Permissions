#!/usr/bin/env python3
"""
Tamnoon GCP Onboarding - Permission Assignment Script

Run in Google Cloud Shell to assign required Tamnoon permissions.

Usage:
    python3 poc_onboarding.py                              # Interactive mode
    python3 poc_onboarding.py --help                       # Show help
    python3 poc_onboarding.py --scope organization --org-id 123456789
    python3 poc_onboarding.py --scope folder --folder-ids 111 222 333
    python3 poc_onboarding.py --scope project --project-ids proj-a proj-b -y
"""

import argparse
import subprocess
import sys

# =============================================================================
# Role Definitions by Scope
# =============================================================================

ORG_ROLES = [
    "roles/resourcemanager.organizationViewer",
    "roles/viewer",
    "roles/logging.privateLogViewer",
    "roles/serviceusage.serviceUsageConsumer",
]

FOLDER_ROLES = [
    "roles/resourcemanager.folderViewer",
    "roles/viewer",
    "roles/logging.privateLogViewer",
    "roles/serviceusage.serviceUsageConsumer",
]

PROJECT_ROLES = [
    "roles/viewer",
    "roles/logging.privateLogViewer",
    "roles/serviceusage.serviceUsageConsumer",
]

DEFAULT_MEMBER = "tamnoonpoc@tamnoon.io"

# =============================================================================
# Helper Functions
# =============================================================================

def run_gcloud(args_list):
    """Execute gcloud command and return (success, output, error)."""
    cmd = ["gcloud"] + args_list
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
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
    # Handle: "id1, id2, id3" or "id1 id2 id3" or "id1,id2,id3"
    input_str = input_str.replace(",", " ")
    return [rid.strip() for rid in input_str.split() if rid.strip()]


def format_member(email, member_type):
    """Format member string for gcloud command."""
    return f"{member_type}:{email}"


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

    # Progress prefix for multiple resources
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


def show_validation_summary(scope_type, resources, member, roles):
    """Display planned actions and return confirmation."""
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

    total_resources = len(results_by_resource)
    all_success = all(r["failed"] == 0 for r in results_by_resource.values())

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
    print("  1. Organization")
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

    # Organization only supports single ID
    if scope_type == "organization" and len(resources) > 1:
        print("Organization scope only supports a single organization ID.")
        resources = [resources[0]]

    # 3. Get member email
    try:
        member_input = input(f"\nEnter member email [{DEFAULT_MEMBER}]: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 1

    member_email = member_input if member_input else DEFAULT_MEMBER

    # 4. Get member type
    try:
        type_input = input("Member type - (u)ser or (s)erviceAccount [u]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 1

    member_type = "serviceAccount" if type_input in ('s', 'serviceaccount') else "user"
    member = format_member(member_email, member_type)

    # 5. Show validation and confirm
    show_validation_summary(scope_type, resources, member, roles)

    if not prompt_confirmation():
        print("Cancelled.")
        return 1

    # 6. Execute
    results_by_resource = {}
    total = len(resources)

    for i, resource_id in enumerate(resources, 1):
        index = i if total > 1 else None
        total_count = total if total > 1 else None
        results = assign_roles_to_resource(scope_type, resource_id, member, roles, index, total_count)
        results_by_resource[resource_id] = results

    # 7. Print summary
    print_summary(scope_type, results_by_resource)

    # Return non-zero if any failures
    if any(r["failed"] > 0 for r in results_by_resource.values()):
        return 1
    return 0


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Tamnoon GCP Onboarding - Assign required permissions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 poc_onboarding.py
  python3 poc_onboarding.py --scope organization --org-id 123456789
  python3 poc_onboarding.py --scope folder --folder-ids 111 222 333
  python3 poc_onboarding.py --scope project --project-ids proj-a proj-b -y
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
    parser.add_argument("--member-type", choices=["user", "serviceAccount"], default="user",
                        help="Member type (default: user)")
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

    member = format_member(args.member, args.member_type)

    # Check authentication
    auth_ok, account = check_gcloud_auth()
    if not auth_ok:
        print(f"Error: Not authenticated with gcloud. {account}")
        print("Please run 'gcloud auth login' first.")
        return 1

    # Show validation summary
    show_validation_summary(args.scope, resources, member, roles)

    # Confirm unless --yes
    if not args.yes:
        if not prompt_confirmation():
            print("Cancelled.")
            return 1

    # Execute
    results_by_resource = {}
    total = len(resources)

    for i, resource_id in enumerate(resources, 1):
        index = i if total > 1 else None
        total_count = total if total > 1 else None
        results = assign_roles_to_resource(args.scope, resource_id, member, roles, index, total_count)
        results_by_resource[resource_id] = results

    # Print summary
    print_summary(args.scope, results_by_resource)

    # Return non-zero if any failures
    if any(r["failed"] > 0 for r in results_by_resource.values()):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
