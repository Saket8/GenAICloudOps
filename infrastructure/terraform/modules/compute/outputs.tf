# Outputs for OCI Compute Module

# Instance outputs (for non-autoscaling deployments)
output "instance_ids" {
  description = "OCIDs of the created compute instances"
  value       = var.enable_autoscaling ? [] : oci_core_instance.instance[*].id
}

output "instance_public_ips" {
  description = "Public IP addresses of the instances"
  value       = var.enable_autoscaling ? [] : oci_core_instance.instance[*].public_ip
}

output "instance_private_ips" {
  description = "Private IP addresses of the instances"
  value       = var.enable_autoscaling ? [] : oci_core_instance.instance[*].private_ip
}

output "instance_display_names" {
  description = "Display names of the instances"
  value       = var.enable_autoscaling ? [] : oci_core_instance.instance[*].display_name
}

# Auto-scaling outputs
output "instance_configuration_id" {
  description = "OCID of the instance configuration (for auto-scaling)"
  value       = var.enable_autoscaling ? oci_core_instance_configuration.instance_config[0].id : null
}

output "instance_pool_id" {
  description = "OCID of the instance pool (for auto-scaling)"
  value       = var.enable_autoscaling ? oci_core_instance_pool.instance_pool[0].id : null
}

output "autoscaling_configuration_id" {
  description = "OCID of the auto-scaling configuration"
  value       = var.enable_autoscaling ? oci_autoscaling_auto_scaling_configuration.autoscaling_config[0].id : null
}

output "instance_pool_size" {
  description = "Current size of the instance pool"
  value       = var.enable_autoscaling ? oci_core_instance_pool.instance_pool[0].size : null
}

# General outputs
output "availability_domains" {
  description = "List of availability domains in the region"
  value       = data.oci_identity_availability_domains.available.availability_domains[*].name
}

output "image_id" {
  description = "OCID of the image used for instances"
  value       = var.custom_image_id != null ? var.custom_image_id : data.oci_core_images.instance_images.images[0].id
}

output "operating_system" {
  description = "Operating system of the instances"
  value       = var.operating_system
}

output "shape" {
  description = "Shape of the instances"
  value       = var.instance_shape
}

# Configuration summary
output "deployment_summary" {
  description = "Summary of the deployment configuration"
  value = {
    deployment_type     = var.enable_autoscaling ? "auto-scaling" : "fixed-size"
    instance_count     = var.enable_autoscaling ? "${var.min_instance_count}-${var.max_instance_count}" : var.instance_count
    shape              = var.instance_shape
    multi_ad           = var.multi_ad_deployment
    auto_scaling_enabled = var.enable_autoscaling
  }
} 