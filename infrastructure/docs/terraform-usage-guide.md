# Terraform Modules Usage Guide

This guide provides comprehensive documentation for using the Terraform modules in the GenAI CloudOps infrastructure automation.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Compute Module](#compute-module)
3. [Networking Module](#networking-module)
4. [Usage Examples](#usage-examples)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Terraform >= 1.0
- OCI CLI configured with proper credentials
- Appropriate IAM permissions in OCI

### Initial Setup

1. **Configure OCI Provider**

```hcl
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 4.0"
    }
  }
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}
```

2. **Set Required Variables**

```hcl
variable "tenancy_ocid" {
  description = "OCID of the tenancy"
  type        = string
}

variable "compartment_ocid" {
  description = "OCID of the compartment"
  type        = string
}

variable "region" {
  description = "OCI region"
  type        = string
  default     = "us-ashburn-1"
}
```

## Compute Module

The compute module provides flexible compute instance deployment with auto-scaling capabilities.

### Basic Usage

```hcl
module "compute" {
  source = "./modules/compute"
  
  compartment_id = var.compartment_ocid
  name_prefix    = "genai-cloudops"
  subnet_id      = module.networking.private_subnet_ids[0]
  ssh_public_key = file("~/.ssh/id_rsa.pub")
  
  # Instance configuration
  instance_shape = "VM.Standard.E4.Flex"
  is_flex_shape  = true
  ocpus          = 2
  memory_in_gbs  = 32
  
  # Single instance deployment
  enable_autoscaling = false
  instance_count     = 3
  
  freeform_tags = {
    Environment = "production"
    Project     = "genai-cloudops"
    Team        = "platform"
  }
}
```

### Auto-Scaling Configuration

```hcl
module "autoscaling_compute" {
  source = "./modules/compute"
  
  compartment_id = var.compartment_ocid
  name_prefix    = "genai-cloudops-auto"
  subnet_id      = module.networking.private_subnet_ids[0]
  ssh_public_key = file("~/.ssh/id_rsa.pub")
  
  # Enable auto-scaling
  enable_autoscaling    = true
  initial_instance_count = 2
  min_instance_count    = 1
  max_instance_count    = 10
  multi_ad_deployment   = true
  
  # Scaling thresholds
  cpu_scale_out_threshold = 75
  cpu_scale_in_threshold  = 25
  scale_out_step         = 2
  scale_in_step          = 1
  cooldown_seconds       = 300
  
  # Custom user data for instance initialization
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    environment = "production"
    app_name    = "genai-cloudops"
  }))
}
```

### Advanced Configuration

```hcl
module "advanced_compute" {
  source = "./modules/compute"
  
  compartment_id = var.compartment_ocid
  name_prefix    = "genai-cloudops-advanced"
  subnet_id      = module.networking.private_subnet_ids[0]
  ssh_public_key = file("~/.ssh/id_rsa.pub")
  
  # High-performance instance configuration
  instance_shape = "VM.Standard.E4.Flex"
  is_flex_shape  = true
  ocpus          = 8
  memory_in_gbs  = 128
  
  # Custom image
  custom_image_id = "ocid1.image.oc1.iad.aaaaaaaa..."
  
  # Network security
  nsg_ids = [
    module.networking.network_security_group_ids[0],
    module.networking.network_security_group_ids[1]
  ]
  
  # No public IP for security
  assign_public_ip = false
  hostname_label   = "advanced-host"
  
  # Environment-specific tags
  defined_tags = {
    "Operations.Environment" = "production"
    "Finance.CostCenter"     = "engineering"
  }
}
```

### Compute Module Outputs

```hcl
# Access instance information
output "instance_ids" {
  value = module.compute.instance_ids
}

output "private_ips" {
  value = module.compute.instance_private_ips
}

output "deployment_summary" {
  value = module.compute.deployment_summary
}
```

## Networking Module

The networking module creates a complete VCN with subnets, gateways, and security configurations.

### Basic VCN Setup

```hcl
module "networking" {
  source = "./modules/networking"
  
  compartment_id = var.compartment_ocid
  name_prefix    = "genai-cloudops"
  
  # VCN configuration
  vcn_cidr_blocks = ["10.0.0.0/16"]
  vcn_dns_label   = "genaivcn"
  
  # Enable all gateways
  create_internet_gateway = true
  create_nat_gateway      = true
  create_service_gateway  = true
  
  # Public subnets (for load balancers, bastion hosts)
  public_subnets = [
    {
      cidr_block          = "10.0.1.0/24"
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
      dns_label          = "public1"
    },
    {
      cidr_block          = "10.0.2.0/24"
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[1].name
      dns_label          = "public2"
    }
  ]
  
  # Private subnets (for application servers, databases)
  private_subnets = [
    {
      cidr_block          = "10.0.10.0/24"
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
      dns_label          = "private1"
    },
    {
      cidr_block          = "10.0.11.0/24"
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[1].name
      dns_label          = "private2"
    }
  ]
}

# Get availability domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}
```

### Custom Security Rules

```hcl
module "custom_networking" {
  source = "./modules/networking"
  
  compartment_id = var.compartment_ocid
  name_prefix    = "genai-cloudops-custom"
  
  # Custom ingress rules for public subnets
  public_ingress_rules = [
    {
      protocol    = "6"  # TCP
      source      = "0.0.0.0/0"
      description = "HTTPS from internet"
      port_min    = 443
      port_max    = 443
    },
    {
      protocol    = "6"  # TCP
      source      = "10.0.0.0/8"
      description = "SSH from private networks"
      port_min    = 22
      port_max    = 22
    }
  ]
  
  # Custom ingress rules for private subnets
  private_ingress_rules = [
    {
      protocol    = "6"  # TCP
      source      = "10.0.0.0/16"
      description = "Application traffic within VCN"
      port_min    = 8080
      port_max    = 8080
    },
    {
      protocol    = "6"  # TCP
      source      = "10.0.0.0/16"
      description = "Database traffic within VCN"
      port_min    = 5432
      port_max    = 5432
    }
  ]
  
  # Network Security Groups with detailed rules
  network_security_groups = [
    {
      name = "web-tier"
      rules = [
        {
          direction   = "INGRESS"
          protocol    = "6"
          source      = "0.0.0.0/0"
          port_min    = 443
          port_max    = 443
          description = "HTTPS from internet"
        },
        {
          direction   = "EGRESS"
          protocol    = "6"
          destination = "10.0.10.0/24"
          port_min    = 8080
          port_max    = 8080
          description = "App tier communication"
        }
      ]
    },
    {
      name = "app-tier"
      rules = [
        {
          direction   = "INGRESS"
          protocol    = "6"
          source      = "10.0.1.0/24"
          port_min    = 8080
          port_max    = 8080
          description = "Web tier traffic"
        },
        {
          direction   = "EGRESS"
          protocol    = "6"
          destination = "10.0.20.0/24"
          port_min    = 5432
          port_max    = 5432
          description = "Database communication"
        }
      ]
    }
  ]
}
```

### Networking Module Outputs

```hcl
# Access network resources
output "vcn_id" {
  value = module.networking.vcn_id
}

output "public_subnet_ids" {
  value = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.networking.private_subnet_ids
}

output "nsg_ids" {
  value = module.networking.network_security_group_ids
}
```

## Usage Examples

### Complete Infrastructure Stack

```hcl
# Complete infrastructure deployment
module "infrastructure" {
  source = "./environments/production"
  
  # Global configuration
  tenancy_ocid     = var.tenancy_ocid
  compartment_ocid = var.compartment_ocid
  region          = "us-ashburn-1"
  
  # Environment-specific configuration
  environment = "production"
  project     = "genai-cloudops"
  
  # Networking configuration
  vcn_cidr         = "10.0.0.0/16"
  enable_bastion   = true
  enable_nat       = true
  
  # Compute configuration
  enable_autoscaling     = true
  min_instances         = 2
  max_instances         = 20
  instance_shape        = "VM.Standard.E4.Flex"
  instance_ocpus        = 4
  instance_memory_gb    = 64
  
  # Security configuration
  ssh_public_key = file("~/.ssh/production_key.pub")
  enable_monitoring = true
  enable_logging   = true
  
  # Tags
  common_tags = {
    Environment = "production"
    Project     = "genai-cloudops"
    ManagedBy   = "terraform"
    CostCenter  = "engineering"
  }
}
```

### Multi-Environment Setup

```hcl
# Development environment
module "dev_infrastructure" {
  source = "./modules"
  
  compartment_id = var.dev_compartment_ocid
  name_prefix    = "genai-cloudops-dev"
  
  # Smaller configuration for development
  networking = {
    vcn_cidr = "10.1.0.0/16"
    public_subnets = ["10.1.1.0/24"]
    private_subnets = ["10.1.10.0/24"]
  }
  
  compute = {
    instance_shape = "VM.Standard.E4.Flex"
    ocpus         = 1
    memory_gb     = 16
    instance_count = 1
    enable_autoscaling = false
  }
  
  tags = {
    Environment = "development"
    AutoShutdown = "true"
  }
}

# Production environment
module "prod_infrastructure" {
  source = "./modules"
  
  compartment_id = var.prod_compartment_ocid
  name_prefix    = "genai-cloudops-prod"
  
  # High-availability configuration
  networking = {
    vcn_cidr = "10.0.0.0/16"
    public_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
    private_subnets = ["10.0.10.0/24", "10.0.11.0/24"]
    multi_ad = true
  }
  
  compute = {
    instance_shape = "VM.Standard.E4.Flex"
    ocpus         = 8
    memory_gb     = 128
    enable_autoscaling = true
    min_instances = 3
    max_instances = 50
  }
  
  tags = {
    Environment = "production"
    HighAvailability = "true"
    BackupRequired = "true"
  }
}
```

## Best Practices

### Security Best Practices

1. **Network Segmentation**
   - Use private subnets for application and database tiers
   - Implement Network Security Groups for fine-grained access control
   - Avoid 0.0.0.0/0 ingress rules where possible

2. **Access Control**
   - Use IAM policies with least privilege principle
   - Implement bastion hosts for SSH access
   - Enable instance agents for monitoring and management

3. **Encryption**
   - Use customer-managed encryption keys
   - Enable encryption for all storage resources
   - Use HTTPS for all web traffic

### Performance Best Practices

1. **Instance Sizing**
   - Use flexible shapes for optimal resource allocation
   - Monitor utilization and adjust sizing accordingly
   - Consider dedicated VM hosts for consistent performance

2. **Auto-Scaling**
   - Set appropriate scaling thresholds
   - Use cooldown periods to prevent thrashing
   - Monitor scaling events and adjust policies

3. **Storage Optimization**
   - Use high-performance storage for databases
   - Implement backup and retention policies
   - Monitor storage utilization

### Cost Optimization

1. **Resource Management**
   - Use auto-scaling to match demand
   - Implement shutdown schedules for non-production environments
   - Monitor unused resources regularly

2. **Tagging Strategy**
   - Implement consistent tagging for cost allocation
   - Use defined tags for governance
   - Track costs by environment and project

## Troubleshooting

### Common Issues

1. **Module Not Found**
   ```bash
   terraform init
   terraform get
   ```

2. **Permission Denied**
   - Verify OCI CLI configuration
   - Check IAM policies
   - Ensure correct compartment permissions

3. **Resource Already Exists**
   ```bash
   terraform import <resource_type>.<resource_name> <ocid>
   ```

4. **Auto-Scaling Not Working**
   - Check monitoring metrics configuration
   - Verify scaling policies
   - Review instance agent status

### Debugging Commands

```bash
# Enable detailed logging
export TF_LOG=DEBUG

# Plan with detailed output
terraform plan -detailed-exitcode

# Apply with auto-approve (use carefully)
terraform apply -auto-approve

# Check state
terraform state list
terraform state show <resource>

# Refresh state
terraform refresh
```

### Getting Help

- Check Terraform OCI Provider documentation
- Review OCI service limits and quotas
- Use OCI Console for resource verification
- Check CloudShell for OCI CLI testing

For module-specific issues, check the individual module documentation and examples in the respective directories. 