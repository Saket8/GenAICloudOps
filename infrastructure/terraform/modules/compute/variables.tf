# Variables for OCI Compute Module

variable "compartment_id" {
  description = "OCID of the compartment where resources will be created"
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "genai-cloudops"
}

variable "subnet_id" {
  description = "OCID of the subnet where instances will be placed"
  type        = string
}

# Instance Configuration
variable "instance_shape" {
  description = "Shape of the compute instance"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "is_flex_shape" {
  description = "Whether the instance shape is flexible"
  type        = bool
  default     = true
}

variable "ocpus" {
  description = "Number of OCPUs for flexible shapes"
  type        = number
  default     = 1
}

variable "memory_in_gbs" {
  description = "Amount of memory in GBs for flexible shapes"
  type        = number
  default     = 16
}

variable "operating_system" {
  description = "Operating system for the instance"
  type        = string
  default     = "Oracle Linux"
}

variable "custom_image_id" {
  description = "Custom image OCID (optional)"
  type        = string
  default     = null
}

# Network Configuration
variable "assign_public_ip" {
  description = "Whether to assign public IP to instances"
  type        = bool
  default     = false
}

variable "hostname_label" {
  description = "Hostname label for the instance"
  type        = string
  default     = "instance"
}

variable "nsg_ids" {
  description = "List of Network Security Group OCIDs"
  type        = list(string)
  default     = []
}

# SSH and User Data
variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

variable "user_data" {
  description = "User data script for instance initialization"
  type        = string
  default     = null
}

# Scaling Configuration
variable "enable_autoscaling" {
  description = "Enable auto-scaling for instances"
  type        = bool
  default     = false
}

variable "instance_count" {
  description = "Number of instances to create (when auto-scaling is disabled)"
  type        = number
  default     = 1
}

variable "initial_instance_count" {
  description = "Initial number of instances in the pool"
  type        = number
  default     = 2
}

variable "min_instance_count" {
  description = "Minimum number of instances in auto-scaling"
  type        = number
  default     = 1
}

variable "max_instance_count" {
  description = "Maximum number of instances in auto-scaling"
  type        = number
  default     = 10
}

variable "multi_ad_deployment" {
  description = "Deploy instances across multiple availability domains"
  type        = bool
  default     = true
}

# Auto-scaling Metrics
variable "cpu_scale_out_threshold" {
  description = "CPU utilization threshold for scaling out (percentage)"
  type        = number
  default     = 80
}

variable "cpu_scale_in_threshold" {
  description = "CPU utilization threshold for scaling in (percentage)"
  type        = number
  default     = 30
}

variable "scale_out_step" {
  description = "Number of instances to add during scale out"
  type        = number
  default     = 2
}

variable "scale_in_step" {
  description = "Number of instances to remove during scale in"
  type        = number
  default     = 1
}

variable "cooldown_seconds" {
  description = "Cooldown period in seconds between scaling actions"
  type        = number
  default     = 300
}

# Tags
variable "defined_tags" {
  description = "Defined tags for the resources"
  type        = map(string)
  default     = {}
}

variable "freeform_tags" {
  description = "Freeform tags for the resources"
  type        = map(string)
  default = {
    "Environment" = "production"
    "Project"     = "genai-cloudops"
    "ManagedBy"   = "terraform"
  }
} 