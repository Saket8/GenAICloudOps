# Complete Infrastructure Example
# This example demonstrates how to deploy a complete infrastructure stack
# using the GenAI CloudOps Terraform modules

terraform {
  required_version = ">= 1.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 4.0"
    }
  }
}

# Provider configuration
provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# Get availability domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

# Generate SSH key pair
resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Save private key to local file
resource "local_file" "private_key" {
  content  = tls_private_key.ssh_key.private_key_pem
  filename = "${path.module}/private_key.pem"
  file_permission = "0600"
}

# Networking Module - Create VCN with public and private subnets
module "networking" {
  source = "../../modules/networking"
  
  compartment_id = var.compartment_ocid
  name_prefix    = var.project_name
  
  # VCN Configuration
  vcn_cidr_blocks = [var.vcn_cidr]
  vcn_dns_label   = "${replace(var.project_name, "-", "")}vcn"
  
  # Enable all gateways for complete connectivity
  create_internet_gateway = true
  create_nat_gateway      = true
  create_service_gateway  = true
  
  # Public subnets for load balancers and bastion hosts
  public_subnets = [
    {
      cidr_block          = cidrsubnet(var.vcn_cidr, 8, 1)
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
      dns_label          = "public1"
    },
    {
      cidr_block          = cidrsubnet(var.vcn_cidr, 8, 2)
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[length(data.oci_identity_availability_domains.ads.availability_domains) > 1 ? 1 : 0].name
      dns_label          = "public2"
    }
  ]
  
  # Private subnets for application servers and databases
  private_subnets = [
    {
      cidr_block          = cidrsubnet(var.vcn_cidr, 8, 10)
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
      dns_label          = "private1"
    },
    {
      cidr_block          = cidrsubnet(var.vcn_cidr, 8, 11)
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[length(data.oci_identity_availability_domains.ads.availability_domains) > 1 ? 1 : 0].name
      dns_label          = "private2"
    }
  ]
  
  # Custom security rules for the application
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
      source      = "0.0.0.0/0"
      description = "HTTP from internet"
      port_min    = 80
      port_max    = 80
    },
    {
      protocol    = "6"  # TCP
      source      = var.admin_cidr
      description = "SSH from admin network"
      port_min    = 22
      port_max    = 22
    }
  ]
  
  private_ingress_rules = [
    {
      protocol    = "6"  # TCP
      source      = var.vcn_cidr
      description = "Application traffic within VCN"
      port_min    = 8080
      port_max    = 8080
    },
    {
      protocol    = "6"  # TCP
      source      = var.vcn_cidr
      description = "Database traffic within VCN"
      port_min    = 5432
      port_max    = 5432
    }
  ]
  
  # Network Security Groups for different tiers
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
          direction   = "INGRESS"
          protocol    = "6"
          source      = "0.0.0.0/0"
          port_min    = 80
          port_max    = 80
          description = "HTTP from internet"
        },
        {
          direction   = "EGRESS"
          protocol    = "6"
          destination = cidrsubnet(var.vcn_cidr, 8, 10)
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
          source      = cidrsubnet(var.vcn_cidr, 8, 1)
          port_min    = 8080
          port_max    = 8080
          description = "Web tier traffic"
        },
        {
          direction   = "INGRESS"
          protocol    = "6"
          source      = cidrsubnet(var.vcn_cidr, 8, 2)
          port_min    = 8080
          port_max    = 8080
          description = "Web tier traffic (AD2)"
        },
        {
          direction   = "EGRESS"
          protocol    = "6"
          destination = cidrsubnet(var.vcn_cidr, 8, 20)
          port_min    = 5432
          port_max    = 5432
          description = "Database communication"
        }
      ]
    },
    {
      name = "database-tier"
      rules = [
        {
          direction   = "INGRESS"
          protocol    = "6"
          source      = cidrsubnet(var.vcn_cidr, 8, 10)
          port_min    = 5432
          port_max    = 5432
          description = "Database access from app tier"
        },
        {
          direction   = "INGRESS"
          protocol    = "6"
          source      = cidrsubnet(var.vcn_cidr, 8, 11)
          port_min    = 5432
          port_max    = 5432
          description = "Database access from app tier (AD2)"
        }
      ]
    }
  ]
  
  # Environment tags
  freeform_tags = merge(var.common_tags, {
    "Tier" = "networking"
  })
}

# Web Tier Compute - Auto-scaling load balancer tier
module "web_tier" {
  source = "../../modules/compute"
  
  compartment_id = var.compartment_ocid
  name_prefix    = "${var.project_name}-web"
  subnet_id      = module.networking.public_subnet_ids[0]
  ssh_public_key = tls_private_key.ssh_key.public_key_openssh
  
  # Instance configuration optimized for web serving
  instance_shape = var.web_tier_shape
  is_flex_shape  = true
  ocpus          = var.web_tier_ocpus
  memory_in_gbs  = var.web_tier_memory_gb
  
  # Enable auto-scaling for web tier
  enable_autoscaling     = true
  initial_instance_count = var.web_tier_initial_count
  min_instance_count     = var.web_tier_min_count
  max_instance_count     = var.web_tier_max_count
  multi_ad_deployment    = true
  
  # Aggressive scaling for web tier
  cpu_scale_out_threshold = 70
  cpu_scale_in_threshold  = 30
  scale_out_step         = 2
  scale_in_step          = 1
  cooldown_seconds       = 300
  
  # Assign public IP for direct internet access
  assign_public_ip = true
  hostname_label   = "web"
  
  # Web tier security group
  nsg_ids = [module.networking.network_security_group_ids[0]]
  
  # User data for web server setup
  user_data = base64encode(templatefile("${path.module}/user-data/web-tier.sh", {
    app_backend_url = "http://${module.networking.private_subnet_cidr_blocks[0]}"
    environment     = var.environment
  }))
  
  freeform_tags = merge(var.common_tags, {
    "Tier" = "web"
    "AutoScaling" = "enabled"
  })
}

# Application Tier Compute - Auto-scaling application servers
module "app_tier" {
  source = "../../modules/compute"
  
  compartment_id = var.compartment_ocid
  name_prefix    = "${var.project_name}-app"
  subnet_id      = module.networking.private_subnet_ids[0]
  ssh_public_key = tls_private_key.ssh_key.public_key_openssh
  
  # Instance configuration for application processing
  instance_shape = var.app_tier_shape
  is_flex_shape  = true
  ocpus          = var.app_tier_ocpus
  memory_in_gbs  = var.app_tier_memory_gb
  
  # Enable auto-scaling for app tier
  enable_autoscaling     = true
  initial_instance_count = var.app_tier_initial_count
  min_instance_count     = var.app_tier_min_count
  max_instance_count     = var.app_tier_max_count
  multi_ad_deployment    = true
  
  # Conservative scaling for app tier
  cpu_scale_out_threshold = 75
  cpu_scale_in_threshold  = 25
  scale_out_step         = 1
  scale_in_step          = 1
  cooldown_seconds       = 600
  
  # No public IP for security
  assign_public_ip = false
  hostname_label   = "app"
  
  # Application tier security group
  nsg_ids = [module.networking.network_security_group_ids[1]]
  
  # User data for application setup
  user_data = base64encode(templatefile("${path.module}/user-data/app-tier.sh", {
    database_host = module.networking.private_subnet_cidr_blocks[1]
    environment   = var.environment
    app_version   = var.app_version
  }))
  
  freeform_tags = merge(var.common_tags, {
    "Tier" = "application"
    "AutoScaling" = "enabled"
  })
}

# Database Tier Compute - Fixed-size database servers
module "database_tier" {
  source = "../../modules/compute"
  
  compartment_id = var.compartment_ocid
  name_prefix    = "${var.project_name}-db"
  subnet_id      = module.networking.private_subnet_ids[1]
  ssh_public_key = tls_private_key.ssh_key.public_key_openssh
  
  # High-performance instance for database
  instance_shape = var.db_tier_shape
  is_flex_shape  = true
  ocpus          = var.db_tier_ocpus
  memory_in_gbs  = var.db_tier_memory_gb
  
  # Fixed deployment for database stability
  enable_autoscaling = false
  instance_count     = var.db_tier_count
  multi_ad_deployment = true
  
  # No public IP for security
  assign_public_ip = false
  hostname_label   = "db"
  
  # Database tier security group
  nsg_ids = [module.networking.network_security_group_ids[2]]
  
  # User data for database setup
  user_data = base64encode(templatefile("${path.module}/user-data/database-tier.sh", {
    db_name     = var.database_name
    environment = var.environment
  }))
  
  freeform_tags = merge(var.common_tags, {
    "Tier" = "database"
    "HighAvailability" = "true"
    "BackupRequired" = "true"
  })
}

# Bastion Host for secure access
module "bastion" {
  source = "../../modules/compute"
  
  compartment_id = var.compartment_ocid
  name_prefix    = "${var.project_name}-bastion"
  subnet_id      = module.networking.public_subnet_ids[0]
  ssh_public_key = tls_private_key.ssh_key.public_key_openssh
  
  # Small instance for bastion
  instance_shape = "VM.Standard.E4.Flex"
  is_flex_shape  = true
  ocpus          = 1
  memory_in_gbs  = 8
  
  # Single bastion instance
  enable_autoscaling = false
  instance_count     = 1
  
  # Public IP for external access
  assign_public_ip = true
  hostname_label   = "bastion"
  
  # User data for bastion setup
  user_data = base64encode(templatefile("${path.module}/user-data/bastion.sh", {
    admin_users = var.admin_users
  }))
  
  freeform_tags = merge(var.common_tags, {
    "Role" = "bastion"
    "SecurityCritical" = "true"
  })
} 