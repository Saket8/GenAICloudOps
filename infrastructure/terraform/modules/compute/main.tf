# Terraform module for OCI Compute instances
# Supports auto-scaling and multiple instance configurations

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 4.0"
    }
  }
}

# Data sources for availability domains and images
data "oci_identity_availability_domains" "available" {
  compartment_id = var.compartment_id
}

data "oci_core_images" "instance_images" {
  compartment_id   = var.compartment_id
  operating_system = var.operating_system
  shape           = var.instance_shape
  state           = "AVAILABLE"
  sort_by         = "TIMECREATED"
  sort_order      = "DESC"
}

# Instance Configuration for Auto Scaling
resource "oci_core_instance_configuration" "instance_config" {
  count          = var.enable_autoscaling ? 1 : 0
  compartment_id = var.compartment_id
  display_name   = "${var.name_prefix}-instance-config"

  instance_details {
    instance_type = "compute"

    launch_details {
      availability_domain = data.oci_identity_availability_domains.available.availability_domains[0].name
      compartment_id      = var.compartment_id
      display_name        = "${var.name_prefix}-instance"
      shape               = var.instance_shape

      dynamic "shape_config" {
        for_each = var.is_flex_shape ? [1] : []
        content {
          ocpus         = var.ocpus
          memory_in_gbs = var.memory_in_gbs
        }
      }

      create_vnic_details {
        subnet_id        = var.subnet_id
        assign_public_ip = var.assign_public_ip
        display_name     = "${var.name_prefix}-vnic"
        hostname_label   = var.hostname_label
        nsg_ids          = var.nsg_ids
      }

      source_details {
        source_type = "image"
        image_id    = var.custom_image_id != null ? var.custom_image_id : data.oci_core_images.instance_images.images[0].id
      }

      metadata = {
        ssh_authorized_keys = var.ssh_public_key
        user_data          = var.user_data != null ? base64encode(var.user_data) : null
      }

      agent_config {
        are_all_plugins_disabled = false
        is_management_disabled   = false
        is_monitoring_disabled   = false

        plugins_config {
          desired_state = "ENABLED"
          name          = "Vulnerability Scanning"
        }

        plugins_config {
          desired_state = "ENABLED"
          name          = "Compute Instance Monitoring"
        }

        plugins_config {
          desired_state = "ENABLED"
          name          = "Bastion"
        }
      }
    }
  }

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Instance Pool for Auto Scaling
resource "oci_core_instance_pool" "instance_pool" {
  count                = var.enable_autoscaling ? 1 : 0
  compartment_id       = var.compartment_id
  instance_configuration_id = oci_core_instance_configuration.instance_config[0].id
  size                 = var.initial_instance_count
  display_name         = "${var.name_prefix}-instance-pool"

  placement_configurations {
    availability_domain = data.oci_identity_availability_domains.available.availability_domains[0].name
    primary_subnet_id   = var.subnet_id
  }

  dynamic "placement_configurations" {
    for_each = var.multi_ad_deployment && length(data.oci_identity_availability_domains.available.availability_domains) > 1 ? [1] : []
    content {
      availability_domain = data.oci_identity_availability_domains.available.availability_domains[1].name
      primary_subnet_id   = var.subnet_id
    }
  }

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Auto Scaling Configuration
resource "oci_autoscaling_auto_scaling_configuration" "autoscaling_config" {
  count               = var.enable_autoscaling ? 1 : 0
  compartment_id      = var.compartment_id
  display_name        = "${var.name_prefix}-autoscaling-config"
  cool_down_in_seconds = var.cooldown_seconds
  is_enabled          = true

  resource {
    id   = oci_core_instance_pool.instance_pool[0].id
    type = "instancePool"
  }

  policies {
    display_name = "${var.name_prefix}-scale-out-policy"
    capacity {
      initial = var.initial_instance_count
      max     = var.max_instance_count
      min     = var.min_instance_count
    }

    policy_type = "threshold"

    rules {
      action {
        type  = "CHANGE_COUNT_BY"
        value = var.scale_out_step
      }
      display_name = "Scale Out Rule"
      metric {
        metric_type = "CPU_UTILIZATION"
        threshold {
          operator = "GT"
          value    = var.cpu_scale_out_threshold
        }
      }
    }

    rules {
      action {
        type  = "CHANGE_COUNT_BY"
        value = -var.scale_in_step
      }
      display_name = "Scale In Rule"
      metric {
        metric_type = "CPU_UTILIZATION"
        threshold {
          operator = "LT"
          value    = var.cpu_scale_in_threshold
        }
      }
    }
  }

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
}

# Single compute instance (when auto-scaling is disabled)
resource "oci_core_instance" "instance" {
  count               = var.enable_autoscaling ? 0 : var.instance_count
  availability_domain = data.oci_identity_availability_domains.available.availability_domains[count.index % length(data.oci_identity_availability_domains.available.availability_domains)].name
  compartment_id      = var.compartment_id
  display_name        = "${var.name_prefix}-instance-${count.index + 1}"
  shape               = var.instance_shape

  dynamic "shape_config" {
    for_each = var.is_flex_shape ? [1] : []
    content {
      ocpus         = var.ocpus
      memory_in_gbs = var.memory_in_gbs
    }
  }

  create_vnic_details {
    subnet_id        = var.subnet_id
    assign_public_ip = var.assign_public_ip
    display_name     = "${var.name_prefix}-vnic-${count.index + 1}"
    hostname_label   = "${var.hostname_label}-${count.index + 1}"
    nsg_ids          = var.nsg_ids
  }

  source_details {
    source_type = "image"
    image_id    = var.custom_image_id != null ? var.custom_image_id : data.oci_core_images.instance_images.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data          = var.user_data != null ? base64encode(var.user_data) : null
  }

  agent_config {
    are_all_plugins_disabled = false
    is_management_disabled   = false
    is_monitoring_disabled   = false

    plugins_config {
      desired_state = "ENABLED"
      name          = "Vulnerability Scanning"
    }

    plugins_config {
      desired_state = "ENABLED"
      name          = "Compute Instance Monitoring"
    }

    plugins_config {
      desired_state = "ENABLED"
      name          = "Bastion"
    }
  }

  defined_tags  = var.defined_tags
  freeform_tags = var.freeform_tags
} 