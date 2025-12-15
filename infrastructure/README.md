# Infrastructure Automation Scripts

This directory contains sample Terraform configurations and OCI CLI scripts for common remediation scenarios in Oracle Cloud Infrastructure (OCI).

## Directory Structure

```
infrastructure/
├── terraform/          # Terraform modules and configurations
│   ├── modules/        # Reusable Terraform modules
│   ├── environments/   # Environment-specific configurations
│   └── examples/       # Example usage scenarios
├── oci-cli/           # OCI CLI automation scripts
│   ├── compute/       # Compute instance management
│   ├── networking/    # Network and security management
│   ├── database/      # Database management
│   ├── monitoring/    # Monitoring and alerting
│   └── utilities/     # Utility scripts
└── docs/              # Documentation and usage guides
```

## Prerequisites

1. **Terraform**: Install Terraform >= 1.0
2. **OCI CLI**: Install and configure OCI CLI
3. **Authentication**: Set up OCI API keys or instance principals
4. **Permissions**: Ensure proper IAM policies are in place

## Usage

Each script and module includes:
- Detailed documentation
- Parameter definitions
- Usage examples
- Environment-specific configurations
- Best practices implementation

## Security

All scripts follow OCI security best practices:
- Use of resource-specific policies
- Encryption at rest and in transit
- Network security controls
- Audit logging enabled

For detailed usage instructions, see the documentation in each subdirectory. 