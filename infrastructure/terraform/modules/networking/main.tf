# Terraform module for OCI Networking
# Creates VCN, subnets, security lists, and network security groups

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 4.0"
    }
  }
}

# Virtual Cloud Network (VCN)
resource "oci_core_vcn" "vcn" {
  compartment_id = var.compartment_id
  display_name   = "${var.name_prefix}-vcn"
  cidr_blocks    = var.vcn_cidr_blocks
  dns_label      = var.vcn_dns_label
  is_ipv6enabled = var.enable_ipv6

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Internet Gateway
resource "oci_core_internet_gateway" "igw" {
  count          = var.create_internet_gateway ? 1 : 0
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.vcn.id
  display_name   = "${var.name_prefix}-igw"
  enabled        = true

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# NAT Gateway
resource "oci_core_nat_gateway" "nat_gateway" {
  count          = var.create_nat_gateway ? 1 : 0
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.vcn.id
  display_name   = "${var.name_prefix}-nat-gateway"
  block_traffic  = false

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Service Gateway
resource "oci_core_service_gateway" "service_gateway" {
  count          = var.create_service_gateway ? 1 : 0
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.vcn.id
  display_name   = "${var.name_prefix}-service-gateway"

  services {
    service_id = data.oci_core_services.all_services.services[0].id
  }

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Data source for OCI services
data "oci_core_services" "all_services" {}

# Public Route Table
resource "oci_core_route_table" "public_route_table" {
  count          = var.create_internet_gateway ? 1 : 0
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.vcn.id
  display_name   = "${var.name_prefix}-public-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.igw[0].id
  }

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Private Route Table
resource "oci_core_route_table" "private_route_table" {
  count          = var.create_nat_gateway ? 1 : 0
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.vcn.id
  display_name   = "${var.name_prefix}-private-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_nat_gateway.nat_gateway[0].id
  }

  dynamic "route_rules" {
    for_each = var.create_service_gateway ? [1] : []
    content {
      destination       = data.oci_core_services.all_services.services[0].cidr_block
      destination_type  = "SERVICE_CIDR_BLOCK"
      network_entity_id = oci_core_service_gateway.service_gateway[0].id
    }
  }

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Public Security List
resource "oci_core_security_list" "public_security_list" {
  count          = length(var.public_subnets) > 0 ? 1 : 0
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.vcn.id
  display_name   = "${var.name_prefix}-public-sl"

  # Egress Rules
  egress_security_rules {
    destination      = "0.0.0.0/0"
    protocol         = "all"
    destination_type = "CIDR_BLOCK"
  }

  # Ingress Rules
  dynamic "ingress_security_rules" {
    for_each = var.public_ingress_rules
    content {
      protocol    = ingress_security_rules.value.protocol
      source      = ingress_security_rules.value.source
      source_type = "CIDR_BLOCK"
      description = ingress_security_rules.value.description

      dynamic "tcp_options" {
        for_each = ingress_security_rules.value.protocol == "6" ? [1] : []
        content {
          min = ingress_security_rules.value.port_min
          max = ingress_security_rules.value.port_max
        }
      }

      dynamic "udp_options" {
        for_each = ingress_security_rules.value.protocol == "17" ? [1] : []
        content {
          min = ingress_security_rules.value.port_min
          max = ingress_security_rules.value.port_max
        }
      }

      dynamic "icmp_options" {
        for_each = ingress_security_rules.value.protocol == "1" ? [1] : []
        content {
          type = ingress_security_rules.value.icmp_type
          code = ingress_security_rules.value.icmp_code
        }
      }
    }
  }

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Private Security List
resource "oci_core_security_list" "private_security_list" {
  count          = length(var.private_subnets) > 0 ? 1 : 0
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.vcn.id
  display_name   = "${var.name_prefix}-private-sl"

  # Egress Rules
  egress_security_rules {
    destination      = "0.0.0.0/0"
    protocol         = "all"
    destination_type = "CIDR_BLOCK"
  }

  # Ingress Rules for VCN traffic
  ingress_security_rules {
    protocol    = "all"
    source      = var.vcn_cidr_blocks[0]
    source_type = "CIDR_BLOCK"
    description = "Allow all traffic within VCN"
  }

  dynamic "ingress_security_rules" {
    for_each = var.private_ingress_rules
    content {
      protocol    = ingress_security_rules.value.protocol
      source      = ingress_security_rules.value.source
      source_type = "CIDR_BLOCK"
      description = ingress_security_rules.value.description

      dynamic "tcp_options" {
        for_each = ingress_security_rules.value.protocol == "6" ? [1] : []
        content {
          min = ingress_security_rules.value.port_min
          max = ingress_security_rules.value.port_max
        }
      }

      dynamic "udp_options" {
        for_each = ingress_security_rules.value.protocol == "17" ? [1] : []
        content {
          min = ingress_security_rules.value.port_min
          max = ingress_security_rules.value.port_max
        }
      }

      dynamic "icmp_options" {
        for_each = ingress_security_rules.value.protocol == "1" ? [1] : []
        content {
          type = ingress_security_rules.value.icmp_type
          code = ingress_security_rules.value.icmp_code
        }
      }
    }
  }

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Public Subnets
resource "oci_core_subnet" "public_subnets" {
  count               = length(var.public_subnets)
  compartment_id      = var.compartment_id
  vcn_id              = oci_core_vcn.vcn.id
  display_name        = "${var.name_prefix}-public-subnet-${count.index + 1}"
  cidr_block          = var.public_subnets[count.index].cidr_block
  availability_domain = var.public_subnets[count.index].availability_domain
  dns_label           = var.public_subnets[count.index].dns_label
  
  route_table_id             = var.create_internet_gateway ? oci_core_route_table.public_route_table[0].id : null
  security_list_ids          = length(var.public_subnets) > 0 ? [oci_core_security_list.public_security_list[0].id] : []
  prohibit_public_ip_on_vnic = false
  prohibit_internet_ingress  = false

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Private Subnets
resource "oci_core_subnet" "private_subnets" {
  count               = length(var.private_subnets)
  compartment_id      = var.compartment_id
  vcn_id              = oci_core_vcn.vcn.id
  display_name        = "${var.name_prefix}-private-subnet-${count.index + 1}"
  cidr_block          = var.private_subnets[count.index].cidr_block
  availability_domain = var.private_subnets[count.index].availability_domain
  dns_label           = var.private_subnets[count.index].dns_label
  
  route_table_id             = var.create_nat_gateway ? oci_core_route_table.private_route_table[0].id : null
  security_list_ids          = length(var.private_subnets) > 0 ? [oci_core_security_list.private_security_list[0].id] : []
  prohibit_public_ip_on_vnic = true
  prohibit_internet_ingress  = true

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Network Security Groups
resource "oci_core_network_security_group" "nsgs" {
  count          = length(var.network_security_groups)
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.vcn.id
  display_name   = "${var.name_prefix}-${var.network_security_groups[count.index].name}-nsg"

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Network Security Group Rules
resource "oci_core_network_security_group_security_rule" "nsg_rules" {
  count                     = length(local.nsg_rules)
  network_security_group_id = oci_core_network_security_group.nsgs[local.nsg_rules[count.index].nsg_index].id
  direction                 = local.nsg_rules[count.index].direction
  protocol                  = local.nsg_rules[count.index].protocol
  description               = local.nsg_rules[count.index].description

  source      = local.nsg_rules[count.index].direction == "INGRESS" ? local.nsg_rules[count.index].source : null
  source_type = local.nsg_rules[count.index].direction == "INGRESS" ? "CIDR_BLOCK" : null

  destination      = local.nsg_rules[count.index].direction == "EGRESS" ? local.nsg_rules[count.index].destination : null
  destination_type = local.nsg_rules[count.index].direction == "EGRESS" ? "CIDR_BLOCK" : null

  dynamic "tcp_options" {
    for_each = local.nsg_rules[count.index].protocol == "6" && local.nsg_rules[count.index].port_min != null ? [1] : []
    content {
      destination_port_range {
        min = local.nsg_rules[count.index].port_min
        max = local.nsg_rules[count.index].port_max
      }
    }
  }

  dynamic "udp_options" {
    for_each = local.nsg_rules[count.index].protocol == "17" && local.nsg_rules[count.index].port_min != null ? [1] : []
    content {
      destination_port_range {
        min = local.nsg_rules[count.index].port_min
        max = local.nsg_rules[count.index].port_max
      }
    }
  }
}

# Local values for flattening NSG rules
locals {
  nsg_rules = flatten([
    for nsg_idx, nsg in var.network_security_groups : [
      for rule in nsg.rules : {
        nsg_index   = nsg_idx
        direction   = rule.direction
        protocol    = rule.protocol
        source      = lookup(rule, "source", null)
        destination = lookup(rule, "destination", null)
        port_min    = lookup(rule, "port_min", null)
        port_max    = lookup(rule, "port_max", null)
        description = rule.description
      }
    ]
  ])
} 