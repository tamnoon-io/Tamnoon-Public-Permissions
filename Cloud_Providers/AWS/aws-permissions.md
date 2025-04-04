Tamnoon requires a role in each monitored AWS account configured with the minimum set of read-only permissions to perform investigations, interrogate cloud resource configurations, and validate activity from log sources.

The `tamnoon-aws-trust-role.yaml` file contains a CloudFormation template that can be deployed into each monitored account.

To use the template, identify the principal ARN that Tamnoon will use for authentication (e.g. Okta group, SSO group, etc.) and submit as a parameter to the template.

