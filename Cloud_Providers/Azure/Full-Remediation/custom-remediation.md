# Tamnoon Azure Remediation Permissions

## Overview

This document outlines the required permissions and role configurations for Azure Resource Manager remediation activities, including both Azure resource management and Entra ID permissions for CIEM (Cloud Infrastructure Entitlement Management) related alert remediation.

## Azure Resource Manager Remediation

Choose one of the following options to configure the appropriate permissions for Azure resource remediation:

### Option 1: Built-in Roles (Recommended)

Deploy built-in roles at **Tenant/Management Groups/Subscriptions scope** using one of these configurations:

#### Primary Option (Preferred)
- **Owner Role** - Provides maximum coverage for all Azure resources and operations

#### Alternative Option
- **Contributor Role** + **Security Admin Role** - Combines resource management with security-specific permissions

**Advantages of Option 1:**
- Quick deployment using Azure's pre-configured roles
- Comprehensive coverage across all Azure services
- No maintenance required for role definitions
- Microsoft-managed and regularly updated

### Option 2: Custom Role Configuration

For organizations requiring more granular control, implement a custom role that includes:

#### Base Permissions
- **Reader Role** - Basic read access across Azure resources
- **Log Analytics Reader Role** - Access to Log Analytics workspaces and queries

#### Extended Custom Role Permissions
The custom role should include permissions for key Azure services (non-exhaustive list):

**Covered Azure Services:**
- Virtual Machines
- Storage Accounts
- App Service
- Network Security Groups
- Container Registry
- Log Analytics
- Cosmos DB
- Key Vault

**Implementation:**
- Reference the attached JSON file for complete custom role definition
- Deploy the custom role at appropriate scope (Tenant/Management Group/Subscription)
- Assign the role to the remediation service principal or user account

**Note:** The provided JSON contains sufficient permissions to cover the key Azure services listed above, but may need expansion for additional services specific to your environment.

## Entra ID Permissions

For CIEM (Cloud Infrastructure Entitlement Management) related alerts remediation, configure one of the following:

### Option 1: Global Administrator (Simplest)
- **Global Administrator** - Directory Role with full administrative access to Entra ID

### Option 2: Directory Readers 

### Option 3: Custom Role Enhancement
Add the following permission to remediation custom-role JSON:
```json
"Microsoft.Authorization/roleAssignments/*"
```

This permission allows management of role assignments, which is essential for CIEM remediation activities.

## Deployment Recommendations

### For Maximum Coverage (Recommended)
1. **Azure Resources:** Deploy **Owner** role at Subscription or Management Group scope
2. **Entra ID:** Assign **Global Administrator** directory role

### For Granular Control
1. **Azure Resources:** Deploy custom role with attached JSON permissions
2. **Entra ID:** Add `Microsoft.Authorization/roleAssignments/*` to custom role JSON

### Scope Considerations
- **Tenant Level:** Maximum coverage across all subscriptions and management groups
- **Management Group Level:** Coverage for specific organizational units
- **Subscription Level:** Targeted coverage for specific subscriptions

## Security Best Practices

1. **Principle of Least Privilege:** Use custom roles when possible to limit permissions to only what's required
2. **Regular Review:** Periodically review and audit assigned permissions
3. **Separation of Duties:** Consider separate accounts for different types of remediation activities
4. **Monitoring:** Enable logging and monitoring for all privileged operations
5. **Time-Limited Access:** Implement PIM (Privileged Identity Management) where applicable

## Implementation Checklist

- [ ] Choose between Option 1 (Built-in) or Option 2 (Custom) roles
- [ ] Determine appropriate scope (Tenant/Management Group/Subscription)
- [ ] Deploy Azure resource permissions
- [ ] Configure Entra ID permissions
- [ ] Test remediatio