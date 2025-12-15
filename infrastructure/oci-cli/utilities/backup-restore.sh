#!/bin/bash

# OCI CLI Script: Backup and Restore Automation
# Description: Automated backup and restore operations for compute, storage, and databases
# Usage: ./backup-restore.sh [backup|restore|schedule|list] [resource-type] [resource-id]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/oci-backup-restore.log"
BACKUP_CONFIG="${SCRIPT_DIR}/../config/backup-config.json"

# Default values
ACTION="${1:-help}"
RESOURCE_TYPE="${2:-}"
RESOURCE_ID="${3:-}"
COMPARTMENT_ID="${COMPARTMENT_ID:-}"
DRY_RUN="${DRY_RUN:-false}"

# Supported resource types
SUPPORTED_TYPES=("instance" "volume" "database" "boot-volume")

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v oci &> /dev/null; then
        error_exit "OCI CLI not found."
    fi
    
    if [[ -z "${COMPARTMENT_ID}" ]]; then
        error_exit "COMPARTMENT_ID environment variable is required."
    fi
    
    log "Prerequisites check completed."
}

# Create default backup configuration
create_default_backup_config() {
    local config_file="$1"
    
    log "Creating default backup configuration..."
    
    mkdir -p "$(dirname "${config_file}")"
    
    cat > "${config_file}" << 'EOF'
{
  "backup_policies": {
    "daily": {
      "description": "Daily backup policy",
      "retention_days": 7,
      "schedule": "0 2 * * *"
    },
    "weekly": {
      "description": "Weekly backup policy", 
      "retention_days": 30,
      "schedule": "0 3 * * 0"
    },
    "monthly": {
      "description": "Monthly backup policy",
      "retention_days": 365,
      "schedule": "0 4 1 * *"
    }
  },
  "resource_defaults": {
    "instance": {
      "policy": "daily",
      "include_boot_volume": true,
      "include_attached_volumes": true
    },
    "volume": {
      "policy": "daily",
      "incremental": true
    },
    "database": {
      "policy": "daily",
      "backup_type": "INCREMENTAL"
    }
  },
  "notifications": {
    "on_success": true,
    "on_failure": true,
    "topic_id": ""
  }
}
EOF
    
    log "Default backup configuration created at: ${config_file}"
}

# Backup compute instance
backup_instance() {
    local instance_id="$1"
    local backup_name="${2:-auto-backup-$(date +%Y%m%d-%H%M%S)}"
    
    log "Creating backup for instance: ${instance_id}"
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would create backup ${backup_name} for instance ${instance_id}"
        return 0
    fi
    
    # Get instance information
    local instance_info
    instance_info=$(oci compute instance get \
        --instance-id "${instance_id}" \
        --query 'data.{name:"display-name",state:"lifecycle-state"}' \
        --output json)
    
    local instance_name
    local instance_state
    instance_name=$(echo "${instance_info}" | jq -r '.name')
    instance_state=$(echo "${instance_info}" | jq -r '.state')
    
    log "Instance: ${instance_name}, State: ${instance_state}"
    
    # Create instance image
    local image_id
    image_id=$(oci compute image create \
        --compartment-id "${COMPARTMENT_ID}" \
        --instance-id "${instance_id}" \
        --display-name "${backup_name}" \
        --wait-for-state AVAILABLE \
        --max-wait-seconds 3600 \
        --query 'data.id' \
        --raw-output)
    
    if [[ $? -eq 0 ]]; then
        log "Instance backup created successfully: ${backup_name} (Image ID: ${image_id})"
        
        # Backup attached volumes if configured
        backup_attached_volumes "${instance_id}" "${backup_name}"
        
        send_notification "Backup Success" "Instance backup ${backup_name} created successfully"
        echo "${image_id}"
    else
        error_exit "Failed to create instance backup"
    fi
}

# Backup attached volumes
backup_attached_volumes() {
    local instance_id="$1"
    local backup_prefix="$2"
    
    log "Backing up volumes attached to instance: ${instance_id}"
    
    # Get attached volumes
    local volume_attachments
    volume_attachments=$(oci compute volume-attachment list \
        --compartment-id "${COMPARTMENT_ID}" \
        --instance-id "${instance_id}" \
        --lifecycle-state ATTACHED \
        --query 'data[].{"volume-id":"volume-id","display-name":"display-name"}' \
        --output json)
    
    echo "${volume_attachments}" | jq -r '.[] | @base64' | while IFS= read -r attachment_data; do
        local attachment
        attachment=$(echo "${attachment_data}" | base64 --decode)
        
        local volume_id
        local volume_name
        volume_id=$(echo "${attachment}" | jq -r '."volume-id"')
        volume_name=$(echo "${attachment}" | jq -r '."display-name"')
        
        local volume_backup_name="${backup_prefix}-vol-${volume_name}-$(date +%Y%m%d-%H%M%S)"
        backup_volume "${volume_id}" "${volume_backup_name}"
    done
}

# Backup block volume
backup_volume() {
    local volume_id="$1"
    local backup_name="${2:-auto-backup-$(date +%Y%m%d-%H%M%S)}"
    local backup_type="${3:-INCREMENTAL}"
    
    log "Creating ${backup_type} backup for volume: ${volume_id}"
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would create ${backup_type} backup ${backup_name} for volume ${volume_id}"
        return 0
    fi
    
    local backup_id
    backup_id=$(oci bv backup create \
        --volume-id "${volume_id}" \
        --display-name "${backup_name}" \
        --type "${backup_type}" \
        --wait-for-state AVAILABLE \
        --max-wait-seconds 3600 \
        --query 'data.id' \
        --raw-output)
    
    if [[ $? -eq 0 ]]; then
        log "Volume backup created successfully: ${backup_name} (Backup ID: ${backup_id})"
        echo "${backup_id}"
    else
        error_exit "Failed to create volume backup"
    fi
}

# Backup database
backup_database() {
    local database_id="$1"
    local backup_name="${2:-auto-backup-$(date +%Y%m%d-%H%M%S)}"
    local backup_type="${3:-INCREMENTAL}"
    
    log "Creating ${backup_type} backup for database: ${database_id}"
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would create ${backup_type} backup ${backup_name} for database ${database_id}"
        return 0
    fi
    
    local backup_id
    backup_id=$(oci db backup create \
        --database-id "${database_id}" \
        --display-name "${backup_name}" \
        --type "${backup_type}" \
        --wait-for-state ACTIVE \
        --max-wait-seconds 3600 \
        --query 'data.id' \
        --raw-output)
    
    if [[ $? -eq 0 ]]; then
        log "Database backup created successfully: ${backup_name} (Backup ID: ${backup_id})"
        echo "${backup_id}"
    else
        error_exit "Failed to create database backup"
    fi
}

# Restore from instance image
restore_instance() {
    local image_id="$1"
    local restore_name="${2:-restored-instance-$(date +%Y%m%d-%H%M%S)}"
    local subnet_id="${3:-}"
    
    if [[ -z "${subnet_id}" ]]; then
        error_exit "Subnet ID is required for instance restore"
    fi
    
    log "Restoring instance from image: ${image_id}"
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would restore instance ${restore_name} from image ${image_id}"
        return 0
    fi
    
    # Get availability domain
    local availability_domain
    availability_domain=$(oci iam availability-domain list \
        --compartment-id "${COMPARTMENT_ID}" \
        --query 'data[0].name' \
        --raw-output)
    
    # Get image information for shape
    local image_info
    image_info=$(oci compute image get \
        --image-id "${image_id}" \
        --query 'data.{shape:"agent-features"."management-supported-shapes"}' \
        --output json)
    
    # Create instance from image
    local instance_id
    instance_id=$(oci compute instance launch \
        --compartment-id "${COMPARTMENT_ID}" \
        --availability-domain "${availability_domain}" \
        --display-name "${restore_name}" \
        --image-id "${image_id}" \
        --shape "VM.Standard.E4.Flex" \
        --shape-config '{"ocpus": 1, "memory_in_gbs": 16}' \
        --subnet-id "${subnet_id}" \
        --assign-public-ip false \
        --wait-for-state RUNNING \
        --max-wait-seconds 1800 \
        --query 'data.id' \
        --raw-output)
    
    if [[ $? -eq 0 ]]; then
        log "Instance restored successfully: ${restore_name} (Instance ID: ${instance_id})"
        send_notification "Restore Success" "Instance ${restore_name} restored from backup"
        echo "${instance_id}"
    else
        error_exit "Failed to restore instance"
    fi
}

# Restore volume from backup
restore_volume() {
    local backup_id="$1"
    local restore_name="${2:-restored-volume-$(date +%Y%m%d-%H%M%S)}"
    local availability_domain="${3:-}"
    
    if [[ -z "${availability_domain}" ]]; then
        availability_domain=$(oci iam availability-domain list \
            --compartment-id "${COMPARTMENT_ID}" \
            --query 'data[0].name' \
            --raw-output)
    fi
    
    log "Restoring volume from backup: ${backup_id}"
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would restore volume ${restore_name} from backup ${backup_id}"
        return 0
    fi
    
    local volume_id
    volume_id=$(oci bv volume create \
        --compartment-id "${COMPARTMENT_ID}" \
        --availability-domain "${availability_domain}" \
        --display-name "${restore_name}" \
        --source-details '{"type": "volumeBackup", "id": "'${backup_id}'"}' \
        --wait-for-state AVAILABLE \
        --max-wait-seconds 1800 \
        --query 'data.id' \
        --raw-output)
    
    if [[ $? -eq 0 ]]; then
        log "Volume restored successfully: ${restore_name} (Volume ID: ${volume_id})"
        echo "${volume_id}"
    else
        error_exit "Failed to restore volume"
    fi
}

# List backups
list_backups() {
    local resource_type="$1"
    
    log "Listing ${resource_type} backups..."
    
    case "${resource_type}" in
        "instance")
            oci compute image list \
                --compartment-id "${COMPARTMENT_ID}" \
                --lifecycle-state AVAILABLE \
                --query 'data[].{id:id,name:"display-name",created:"time-created",state:"lifecycle-state"}' \
                --output table
            ;;
        "volume")
            oci bv backup list \
                --compartment-id "${COMPARTMENT_ID}" \
                --lifecycle-state AVAILABLE \
                --query 'data[].{id:id,name:"display-name",type:type,created:"time-created",size:"size-in-gbs"}' \
                --output table
            ;;
        "database")
            oci db backup list \
                --compartment-id "${COMPARTMENT_ID}" \
                --lifecycle-state ACTIVE \
                --query 'data[].{id:id,name:"display-name",type:type,created:"time-created"}' \
                --output table
            ;;
        *)
            log "Listing all backup types..."
            echo "=== Instance Images ==="
            list_backups "instance"
            echo ""
            echo "=== Volume Backups ==="
            list_backups "volume"
            echo ""
            echo "=== Database Backups ==="
            list_backups "database"
            ;;
    esac
}

# Schedule automated backups
schedule_backups() {
    log "Setting up scheduled backup automation..."
    
    if [[ ! -f "${BACKUP_CONFIG}" ]]; then
        create_default_backup_config "${BACKUP_CONFIG}"
        log "Please update the configuration file and run the script again."
        return 0
    fi
    
    local cron_file="/tmp/oci-backup-cron"
    local script_path="${SCRIPT_DIR}/backup-restore.sh"
    
    # Read configuration
    local daily_schedule
    local weekly_schedule
    local monthly_schedule
    
    daily_schedule=$(jq -r '.backup_policies.daily.schedule' "${BACKUP_CONFIG}")
    weekly_schedule=$(jq -r '.backup_policies.weekly.schedule' "${BACKUP_CONFIG}")
    monthly_schedule=$(jq -r '.backup_policies.monthly.schedule' "${BACKUP_CONFIG}")
    
    # Create cron jobs
    cat > "${cron_file}" << EOF
# OCI Automated Backups
${daily_schedule} COMPARTMENT_ID=${COMPARTMENT_ID} ${script_path} backup-all daily >> ${LOG_FILE} 2>&1
${weekly_schedule} COMPARTMENT_ID=${COMPARTMENT_ID} ${script_path} backup-all weekly >> ${LOG_FILE} 2>&1
${monthly_schedule} COMPARTMENT_ID=${COMPARTMENT_ID} ${script_path} backup-all monthly >> ${LOG_FILE} 2>&1
EOF
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would install cron jobs:"
        cat "${cron_file}"
    else
        crontab "${cron_file}"
        log "Backup schedule installed successfully"
    fi
    
    rm -f "${cron_file}"
}

# Send notification
send_notification() {
    local title="$1"
    local message="$2"
    
    log "NOTIFICATION: ${title} - ${message}"
    
    if [[ -n "${NOTIFICATION_TOPIC_ID:-}" ]]; then
        oci ons message publish \
            --topic-id "${NOTIFICATION_TOPIC_ID}" \
            --message "${message}" \
            --title "OCI Backup/Restore: ${title}" \
            --compartment-id "${COMPARTMENT_ID}" || true
    fi
}

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [ACTION] [RESOURCE_TYPE] [RESOURCE_ID] [OPTIONS]

Actions:
  backup      - Create backup of specified resource
  restore     - Restore from backup
  list        - List available backups
  schedule    - Set up automated backup schedule
  help        - Show this help message

Resource Types:
  instance    - Compute instance
  volume      - Block volume
  database    - Database
  boot-volume - Boot volume

Environment Variables:
  COMPARTMENT_ID        - OCI Compartment ID (required)
  DRY_RUN              - Set to 'true' for dry run mode
  NOTIFICATION_TOPIC_ID - OCI Notifications Topic ID (optional)

Examples:
  $0 backup instance ocid1.instance.oc1.iad.xxx
  $0 backup volume ocid1.volume.oc1.iad.xxx
  $0 restore instance ocid1.image.oc1.iad.xxx subnet-ocid
  $0 list volume
  $0 schedule
  
Configuration file: ${BACKUP_CONFIG}

EOF
}

# Main execution
main() {
    log "Starting OCI Backup/Restore Script"
    log "Action: ${ACTION}, Resource Type: ${RESOURCE_TYPE}, Resource ID: ${RESOURCE_ID}"
    
    check_prerequisites
    
    case "${ACTION}" in
        "backup")
            if [[ -z "${RESOURCE_TYPE}" ]] || [[ -z "${RESOURCE_ID}" ]]; then
                error_exit "Resource type and resource ID are required for backup action."
            fi
            
            if [[ ! " ${SUPPORTED_TYPES[*]} " =~ " ${RESOURCE_TYPE} " ]]; then
                error_exit "Unsupported resource type: ${RESOURCE_TYPE}"
            fi
            
            case "${RESOURCE_TYPE}" in
                "instance")
                    backup_instance "${RESOURCE_ID}"
                    ;;
                "volume"|"boot-volume")
                    backup_volume "${RESOURCE_ID}"
                    ;;
                "database")
                    backup_database "${RESOURCE_ID}"
                    ;;
            esac
            ;;
        "restore")
            if [[ -z "${RESOURCE_TYPE}" ]] || [[ -z "${RESOURCE_ID}" ]]; then
                error_exit "Resource type and backup ID are required for restore action."
            fi
            
            case "${RESOURCE_TYPE}" in
                "instance")
                    local subnet_id="${4:-}"
                    restore_instance "${RESOURCE_ID}" "" "${subnet_id}"
                    ;;
                "volume"|"boot-volume")
                    restore_volume "${RESOURCE_ID}"
                    ;;
                *)
                    error_exit "Restore not yet implemented for ${RESOURCE_TYPE}"
                    ;;
            esac
            ;;
        "list")
            list_backups "${RESOURCE_TYPE:-all}"
            ;;
        "schedule")
            schedule_backups
            ;;
        "help"|*)
            show_usage
            exit 0
            ;;
    esac
    
    log "OCI Backup/Restore Script completed successfully"
}

# Execute main function
main "$@" 