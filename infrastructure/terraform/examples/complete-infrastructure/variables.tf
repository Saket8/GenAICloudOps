# Variables for Complete Infrastructure Example

# OCI Provider Variables
variable "tenancy_ocid" {
  description = "OCID of the tenancy"
  type        = string
}

variable "user_ocid" {
  description = "OCID of the user"
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint of the API key"
  type        = string
}

variable "private_key_path" {
  description = "Path to the private key file"
  type        = string
}

variable "region" {
  description = "OCI region"
  type        = string
  default     = "us-ashburn-1"
}

variable "compartment_ocid" {
  description = "OCID of the compartment where resources will be created"
  type        = string
}

# Project Configuration
variable "project_name" {
  description = "Name of the project (used as prefix for resources)"
  type        = string
  default     = "genai-cloudops"
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9-]*$", var.project_name))
    error_message = "Project name must start with a letter and contain only letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "app_version" {
  description = "Application version to deploy"
  type        = string
  default     = "1.0.0"
}

# Network Configuration
variable "vcn_cidr" {
  description = "CIDR block for the VCN"
  type        = string
  default     = "10.0.0.0/16"
  validation {
    condition     = can(cidrhost(var.vcn_cidr, 0))
    error_message = "VCN CIDR must be a valid IPv4 CIDR block."
  }
}

variable "admin_cidr" {
  description = "CIDR block for admin access (SSH, etc.)"
  type        = string
  default     = "10.0.0.0/8"
}

# Web Tier Configuration
variable "web_tier_shape" {
  description = "Shape for web tier instances"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "web_tier_ocpus" {
  description = "Number of OCPUs for web tier instances"
  type        = number
  default     = 2
  validation {
    condition     = var.web_tier_ocpus >= 1 && var.web_tier_ocpus <= 64
    error_message = "Web tier OCPUs must be between 1 and 64."
  }
}

variable "web_tier_memory_gb" {
  description = "Memory in GB for web tier instances"
  type        = number
  default     = 32
  validation {
    condition     = var.web_tier_memory_gb >= 1 && var.web_tier_memory_gb <= 1024
    error_message = "Web tier memory must be between 1 and 1024 GB."
  }
}

variable "web_tier_initial_count" {
  description = "Initial number of web tier instances"
  type        = number
  default     = 2
}

variable "web_tier_min_count" {
  description = "Minimum number of web tier instances"
  type        = number
  default     = 1
}

variable "web_tier_max_count" {
  description = "Maximum number of web tier instances"
  type        = number
  default     = 20
}

# Application Tier Configuration
variable "app_tier_shape" {
  description = "Shape for application tier instances"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "app_tier_ocpus" {
  description = "Number of OCPUs for application tier instances"
  type        = number
  default     = 4
  validation {
    condition     = var.app_tier_ocpus >= 1 && var.app_tier_ocpus <= 64
    error_message = "Application tier OCPUs must be between 1 and 64."
  }
}

variable "app_tier_memory_gb" {
  description = "Memory in GB for application tier instances"
  type        = number
  default     = 64
  validation {
    condition     = var.app_tier_memory_gb >= 1 && var.app_tier_memory_gb <= 1024
    error_message = "Application tier memory must be between 1 and 1024 GB."
  }
}

variable "app_tier_initial_count" {
  description = "Initial number of application tier instances"
  type        = number
  default     = 3
}

variable "app_tier_min_count" {
  description = "Minimum number of application tier instances"
  type        = number
  default     = 2
}

variable "app_tier_max_count" {
  description = "Maximum number of application tier instances"
  type        = number
  default     = 30
}

# Database Tier Configuration
variable "db_tier_shape" {
  description = "Shape for database tier instances"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "db_tier_ocpus" {
  description = "Number of OCPUs for database tier instances"
  type        = number
  default     = 8
  validation {
    condition     = var.db_tier_ocpus >= 1 && var.db_tier_ocpus <= 64
    error_message = "Database tier OCPUs must be between 1 and 64."
  }
}

variable "db_tier_memory_gb" {
  description = "Memory in GB for database tier instances"
  type        = number
  default     = 128
  validation {
    condition     = var.db_tier_memory_gb >= 1 && var.db_tier_memory_gb <= 1024
    error_message = "Database tier memory must be between 1 and 1024 GB."
  }
}

variable "db_tier_count" {
  description = "Number of database tier instances"
  type        = number
  default     = 2
  validation {
    condition     = var.db_tier_count >= 1 && var.db_tier_count <= 10
    error_message = "Database tier count must be between 1 and 10."
  }
}

variable "database_name" {
  description = "Name of the database"
  type        = string
  default     = "genaidb"
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9]*$", var.database_name))
    error_message = "Database name must start with a letter and contain only letters and numbers."
  }
}

# Admin Configuration
variable "admin_users" {
  description = "List of admin users for bastion host"
  type        = list(string)
  default     = ["admin", "operator"]
}

# Tags
variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    "Environment" = "production"
    "Project"     = "genai-cloudops"
    "ManagedBy"   = "terraform"
    "Owner"       = "platform-team"
    "CostCenter"  = "engineering"
  }
}

# Optional: Enable features
variable "enable_monitoring" {
  description = "Enable comprehensive monitoring and alerting"
  type        = bool
  default     = true
}

variable "enable_backup" {
  description = "Enable automated backup for all tiers"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable centralized logging"
  type        = bool
  default     = true
}

# Cost Optimization
variable "enable_auto_shutdown" {
  description = "Enable automatic shutdown for non-production environments"
  type        = bool
  default     = false
}

variable "auto_shutdown_schedule" {
  description = "Cron schedule for automatic shutdown (only if enabled)"
  type        = string
  default     = "0 22 * * 1-5"  # 10 PM on weekdays
}

# Security
variable "enable_waf" {
  description = "Enable Web Application Firewall"
  type        = bool
  default     = true
}

variable "enable_security_monitoring" {
  description = "Enable security monitoring and alerting"
  type        = bool
  default     = true
}

variable "allowed_ssh_sources" {
  description = "List of CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

# Performance
variable "enable_high_performance_storage" {
  description = "Enable high performance storage for database tier"
  type        = bool
  default     = true
}

variable "enable_load_balancer" {
  description = "Enable load balancer for web tier"
  type        = bool
  default     = true
}

# Disaster Recovery
variable "enable_cross_region_backup" {
  description = "Enable cross-region backup for disaster recovery"
  type        = bool
  default     = false
}

variable "backup_region" {
  description = "Region for cross-region backup"
  type        = string
  default     = "us-phoenix-1"
} 