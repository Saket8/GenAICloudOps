# Outputs for OCI Networking Module

# VCN Outputs
output "vcn_id" {
  description = "OCID of the VCN"
  value       = oci_core_vcn.vcn.id
}

output "vcn_cidr_blocks" {
  description = "CIDR blocks of the VCN"
  value       = oci_core_vcn.vcn.cidr_blocks
}

output "vcn_dns_label" {
  description = "DNS label of the VCN"
  value       = oci_core_vcn.vcn.dns_label
}

output "vcn_default_dhcp_options_id" {
  description = "OCID of the default DHCP options"
  value       = oci_core_vcn.vcn.default_dhcp_options_id
}

output "vcn_default_security_list_id" {
  description = "OCID of the default security list"
  value       = oci_core_vcn.vcn.default_security_list_id
}

# Gateway Outputs
output "internet_gateway_id" {
  description = "OCID of the Internet Gateway"
  value       = var.create_internet_gateway ? oci_core_internet_gateway.igw[0].id : null
}

output "nat_gateway_id" {
  description = "OCID of the NAT Gateway"
  value       = var.create_nat_gateway ? oci_core_nat_gateway.nat_gateway[0].id : null
}

output "service_gateway_id" {
  description = "OCID of the Service Gateway"
  value       = var.create_service_gateway ? oci_core_service_gateway.service_gateway[0].id : null
}

# Route Table Outputs
output "public_route_table_id" {
  description = "OCID of the public route table"
  value       = var.create_internet_gateway ? oci_core_route_table.public_route_table[0].id : null
}

output "private_route_table_id" {
  description = "OCID of the private route table"
  value       = var.create_nat_gateway ? oci_core_route_table.private_route_table[0].id : null
}

# Security List Outputs
output "public_security_list_id" {
  description = "OCID of the public security list"
  value       = length(var.public_subnets) > 0 ? oci_core_security_list.public_security_list[0].id : null
}

output "private_security_list_id" {
  description = "OCID of the private security list"
  value       = length(var.private_subnets) > 0 ? oci_core_security_list.private_security_list[0].id : null
}

# Subnet Outputs
output "public_subnet_ids" {
  description = "OCIDs of the public subnets"
  value       = oci_core_subnet.public_subnets[*].id
}

output "private_subnet_ids" {
  description = "OCIDs of the private subnets"
  value       = oci_core_subnet.private_subnets[*].id
}

output "public_subnet_cidr_blocks" {
  description = "CIDR blocks of the public subnets"
  value       = oci_core_subnet.public_subnets[*].cidr_block
}

output "private_subnet_cidr_blocks" {
  description = "CIDR blocks of the private subnets"
  value       = oci_core_subnet.private_subnets[*].cidr_block
}

output "public_subnets_details" {
  description = "Detailed information about public subnets"
  value = [
    for subnet in oci_core_subnet.public_subnets : {
      id                  = subnet.id
      display_name        = subnet.display_name
      cidr_block         = subnet.cidr_block
      availability_domain = subnet.availability_domain
      dns_label          = subnet.dns_label
    }
  ]
}

output "private_subnets_details" {
  description = "Detailed information about private subnets"
  value = [
    for subnet in oci_core_subnet.private_subnets : {
      id                  = subnet.id
      display_name        = subnet.display_name
      cidr_block         = subnet.cidr_block
      availability_domain = subnet.availability_domain
      dns_label          = subnet.dns_label
    }
  ]
}

# Network Security Group Outputs
output "network_security_group_ids" {
  description = "OCIDs of the Network Security Groups"
  value       = oci_core_network_security_group.nsgs[*].id
}

output "network_security_groups_details" {
  description = "Detailed information about Network Security Groups"
  value = [
    for idx, nsg in oci_core_network_security_group.nsgs : {
      id           = nsg.id
      display_name = nsg.display_name
      name         = var.network_security_groups[idx].name
    }
  ]
}

# Summary Output
output "network_summary" {
  description = "Summary of the network configuration"
  value = {
    vcn_id                  = oci_core_vcn.vcn.id
    vcn_cidr               = oci_core_vcn.vcn.cidr_blocks[0]
    public_subnets_count   = length(oci_core_subnet.public_subnets)
    private_subnets_count  = length(oci_core_subnet.private_subnets)
    internet_gateway_enabled = var.create_internet_gateway
    nat_gateway_enabled     = var.create_nat_gateway
    service_gateway_enabled = var.create_service_gateway
    nsg_count              = length(oci_core_network_security_group.nsgs)
  }
} 