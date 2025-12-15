# Variables for OCI Networking Module

variable "compartment_id" {
  description = "OCID of the compartment where resources will be created"
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "genai-cloudops"
}

# VCN Configuration
variable "vcn_cidr_blocks" {
  description = "List of IPv4 CIDR blocks for the VCN"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "vcn_dns_label" {
  description = "DNS label for the VCN"
  type        = string
  default     = "vcn"
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9]{0,14}$", var.vcn_dns_label))
    error_message = "DNS label must be 1-15 characters, start with a letter, and contain only letters and numbers."
  }
}

variable "enable_ipv6" {
  description = "Enable IPv6 for the VCN"
  type        = bool
  default     = false
}

# Gateway Configuration
variable "create_internet_gateway" {
  description = "Create an Internet Gateway"
  type        = bool
  default     = true
}

variable "create_nat_gateway" {
  description = "Create a NAT Gateway"
  type        = bool
  default     = true
}

variable "create_service_gateway" {
  description = "Create a Service Gateway"
  type        = bool
  default     = true
}

# Subnet Configuration
variable "public_subnets" {
  description = "List of public subnet configurations"
  type = list(object({
    cidr_block          = string
    availability_domain = string
    dns_label          = string
  }))
  default = []
}

variable "private_subnets" {
  description = "List of private subnet configurations"
  type = list(object({
    cidr_block          = string
    availability_domain = string
    dns_label          = string
  }))
  default = []
}

# Security Rules Configuration
variable "public_ingress_rules" {
  description = "List of ingress rules for public security list"
  type = list(object({
    protocol    = string
    source      = string
    description = string
    port_min    = optional(number)
    port_max    = optional(number)
    icmp_type   = optional(number)
    icmp_code   = optional(number)
  }))
  default = [
    {
      protocol    = "6"
      source      = "0.0.0.0/0"
      description = "Allow HTTP"
      port_min    = 80
      port_max    = 80
    },
    {
      protocol    = "6"
      source      = "0.0.0.0/0"
      description = "Allow HTTPS"
      port_min    = 443
      port_max    = 443
    },
    {
      protocol    = "6"
      source      = "0.0.0.0/0"
      description = "Allow SSH"
      port_min    = 22
      port_max    = 22
    }
  ]
}

variable "private_ingress_rules" {
  description = "List of ingress rules for private security list"
  type = list(object({
    protocol    = string
    source      = string
    description = string
    port_min    = optional(number)
    port_max    = optional(number)
    icmp_type   = optional(number)
    icmp_code   = optional(number)
  }))
  default = [
    {
      protocol    = "6"
      source      = "10.0.0.0/16"
      description = "Allow internal HTTP"
      port_min    = 8080
      port_max    = 8080
    },
    {
      protocol    = "6"
      source      = "10.0.0.0/16"
      description = "Allow internal database"
      port_min    = 5432
      port_max    = 5432
    }
  ]
}

# Network Security Groups
variable "network_security_groups" {
  description = "List of Network Security Groups with their rules"
  type = list(object({
    name = string
    rules = list(object({
      direction   = string
      protocol    = string
      source      = optional(string)
      destination = optional(string)
      port_min    = optional(number)
      port_max    = optional(number)
      description = string
    }))
  }))
  default = [
    {
      name = "web-server"
      rules = [
        {
          direction   = "INGRESS"
          protocol    = "6"
          source      = "0.0.0.0/0"
          port_min    = 80
          port_max    = 80
          description = "Allow HTTP from internet"
        },
        {
          direction   = "INGRESS"
          protocol    = "6"
          source      = "0.0.0.0/0"
          port_min    = 443
          port_max    = 443
          description = "Allow HTTPS from internet"
        },
        {
          direction   = "EGRESS"
          protocol    = "all"
          destination = "0.0.0.0/0"
          description = "Allow all outbound traffic"
        }
      ]
    },
    {
      name = "database"
      rules = [
        {
          direction   = "INGRESS"
          protocol    = "6"
          source      = "10.0.0.0/16"
          port_min    = 5432
          port_max    = 5432
          description = "Allow PostgreSQL from VCN"
        },
        {
          direction   = "INGRESS"
          protocol    = "6"
          source      = "10.0.0.0/16"
          port_min    = 3306
          port_max    = 3306
          description = "Allow MySQL from VCN"
        },
        {
          direction   = "EGRESS"
          protocol    = "6"
          destination = "0.0.0.0/0"
          port_min    = 443
          port_max    = 443
          description = "Allow HTTPS outbound for updates"
        }
      ]
    }
  ]
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