#!/bin/bash

# OCI CLI Script: Database Configuration Management
# Description: Automated database operations including backup, scaling, and configuration
# Usage: ./manage-database.sh [backup|scale|configure|monitor] [database-id]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/oci-database.log"

# Default values
ACTION="${1:-help}"
DATABASE_ID="${2:-}"
COMPARTMENT_ID="${COMPARTMENT_ID:-}"
DRY_RUN="${DRY_RUN:-false}"

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
        error_exit "OCI CLI not found. Please install and configure OCI CLI."
    fi
    
    if ! oci iam compartment list --compartment-id-in-subtree true --limit 1 &> /dev/null; then
        error_exit "OCI CLI not properly configured."
    fi
    
    if [[ -z "${COMPARTMENT_ID}" ]]; then
        error_exit "COMPARTMENT_ID environment variable is required."
    fi
    
    log "Prerequisites check completed."
}

# List databases
list_databases() {
    log "Listing databases in compartment ${COMPARTMENT_ID}..."
    
    oci db database list \
        --compartment-id "${COMPARTMENT_ID}" \
        --query 'data[].{id:id,name:"db-name",state:"lifecycle-state",version:"db-version"}' \
        --output table
}

# Get database information
get_database_info() {
    local db_id="$1"
    
    log "Retrieving database information for ${db_id}..."
    
    oci db database get \
        --database-id "${db_id}" \
        --query 'data.{name:"db-name",state:"lifecycle-state",version:"db-version",allocated:"allocated-storage-size-in-gbs"}' \
        --output json
}

# Create database backup
create_backup() {
    local db_id="$1"
    local backup_type="${2:-INCREMENTAL}"  # INCREMENTAL or FULL
    
    log "Creating ${backup_type} backup for database ${db_id}..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would create ${backup_type} backup for database ${db_id}"
        return 0
    fi
    
    local backup_display_name="auto-backup-$(date +%Y%m%d-%H%M%S)"
    
    oci db backup create \
        --database-id "${db_id}" \
        --display-name "${backup_display_name}" \
        --type "${backup_type}" \
        --wait-for-state ACTIVE \
        --max-wait-seconds 3600
    
    if [[ $? -eq 0 ]]; then
        log "Backup created successfully: ${backup_display_name}"
        send_notification "Backup Created" "Database backup ${backup_display_name} created successfully"
    else
        error_exit "Failed to create backup."
    fi
}

# Scale database storage
scale_database_storage() {
    local db_id="$1"
    local new_size_gb="$2"
    
    log "Scaling database storage to ${new_size_gb} GB..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would scale database storage to ${new_size_gb} GB"
        return 0
    fi
    
    # Get DB System ID from database
    local db_system_id
    db_system_id=$(oci db database get \
        --database-id "${db_id}" \
        --query 'data."db-system-id"' \
        --raw-output)
    
    oci db system update \
        --db-system-id "${db_system_id}" \
        --data-storage-size-in-gbs "${new_size_gb}" \
        --wait-for-state AVAILABLE \
        --max-wait-seconds 3600
    
    if [[ $? -eq 0 ]]; then
        log "Database storage scaled successfully to ${new_size_gb} GB"
        send_notification "Storage Scaled" "Database storage scaled to ${new_size_gb} GB"
    else
        error_exit "Failed to scale database storage."
    fi
}

# Configure database parameters
configure_database() {
    local db_id="$1"
    local config_file="${SCRIPT_DIR}/../config/database-config.json"
    
    log "Configuring database parameters..."
    
    if [[ ! -f "${config_file}" ]]; then
        error_exit "Database configuration file not found: ${config_file}"
    fi
    
    # Read configuration parameters
    local parameters
    parameters=$(jq -r '.parameters' "${config_file}")
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would apply database configuration parameters"
        echo "${parameters}" | jq .
        return 0
    fi
    
    # Apply configuration parameters (example for Autonomous Database)
    # Note: This is a simplified example. Actual implementation would depend on database type
    log "Applying database configuration parameters..."
    
    # Example parameters that can be configured
    local cpu_core_count
    local data_storage_size_in_tbs
    local auto_scaling_enabled
    
    cpu_core_count=$(echo "${parameters}" | jq -r '.cpu_core_count // empty')
    data_storage_size_in_tbs=$(echo "${parameters}" | jq -r '.data_storage_size_in_tbs // empty')
    auto_scaling_enabled=$(echo "${parameters}" | jq -r '.auto_scaling_enabled // empty')
    
    local update_cmd="oci db autonomous-database update --autonomous-database-id ${db_id}"
    
    if [[ -n "${cpu_core_count}" ]]; then
        update_cmd+=" --cpu-core-count ${cpu_core_count}"
    fi
    
    if [[ -n "${data_storage_size_in_tbs}" ]]; then
        update_cmd+=" --data-storage-size-in-tbs ${data_storage_size_in_tbs}"
    fi
    
    if [[ -n "${auto_scaling_enabled}" ]]; then
        update_cmd+=" --is-auto-scaling-enabled ${auto_scaling_enabled}"
    fi
    
    update_cmd+=" --wait-for-state AVAILABLE --max-wait-seconds 1800"
    
    eval "${update_cmd}"
    
    if [[ $? -eq 0 ]]; then
        log "Database configuration applied successfully"
        send_notification "Database Configured" "Database configuration parameters applied successfully"
    else
        error_exit "Failed to apply database configuration."
    fi
}

# Monitor database performance
monitor_database() {
    local db_id="$1"
    local duration_minutes="${2:-60}"
    
    log "Monitoring database performance for ${duration_minutes} minutes..."
    
    # Get current time and past time
    local end_time
    local start_time
    end_time=$(date -u '+%Y-%m-%dT%H:%M:%S.000Z')
    start_time=$(date -u -d "${duration_minutes} minutes ago" '+%Y-%m-%dT%H:%M:%S.000Z')
    
    # Query database metrics
    local cpu_metrics
    local storage_metrics
    local connection_metrics
    
    # CPU Utilization
    cpu_metrics=$(oci monitoring metric-data summarize-metrics-data \
        --compartment-id "${COMPARTMENT_ID}" \
        --namespace "oci_autonomous_database" \
        --query-data '[{
            "query": "CpuUtilization[1m].mean()",
            "startTime": "'${start_time}'",
            "endTime": "'${end_time}'",
            "resolution": "PT5M"
        }]' \
        --query 'data[0]."aggregated-datapoints"[-1].value' \
        --raw-output 2>/dev/null || echo "N/A")
    
    # Storage Utilization
    storage_metrics=$(oci monitoring metric-data summarize-metrics-data \
        --compartment-id "${COMPARTMENT_ID}" \
        --namespace "oci_autonomous_database" \
        --query-data '[{
            "query": "StorageUtilization[1m].mean()",
            "startTime": "'${start_time}'",
            "endTime": "'${end_time}'",
            "resolution": "PT5M"
        }]' \
        --query 'data[0]."aggregated-datapoints"[-1].value' \
        --raw-output 2>/dev/null || echo "N/A")
    
    # Connection Count
    connection_metrics=$(oci monitoring metric-data summarize-metrics-data \
        --compartment-id "${COMPARTMENT_ID}" \
        --namespace "oci_autonomous_database" \
        --query-data '[{
            "query": "CurrentConnections[1m].mean()",
            "startTime": "'${start_time}'",
            "endTime": "'${end_time}'",
            "resolution": "PT5M"
        }]' \
        --query 'data[0]."aggregated-datapoints"[-1].value' \
        --raw-output 2>/dev/null || echo "N/A")
    
    # Display monitoring results
    log "Database Performance Metrics (Last ${duration_minutes} minutes):"
    log "  CPU Utilization: ${cpu_metrics}%"
    log "  Storage Utilization: ${storage_metrics}%"
    log "  Current Connections: ${connection_metrics}"
    
    # Check for alerts
    if [[ "${cpu_metrics}" != "N/A" ]] && (( $(echo "${cpu_metrics} > 80" | bc -l) )); then
        log "WARNING: High CPU utilization detected (${cpu_metrics}%)"
        send_notification "High CPU Alert" "Database CPU utilization is ${cpu_metrics}%"
    fi
    
    if [[ "${storage_metrics}" != "N/A" ]] && (( $(echo "${storage_metrics} > 85" | bc -l) )); then
        log "WARNING: High storage utilization detected (${storage_metrics}%)"
        send_notification "High Storage Alert" "Database storage utilization is ${storage_metrics}%"
    fi
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
            --title "OCI Database Management: ${title}" \
            --compartment-id "${COMPARTMENT_ID}" || true
    fi
}

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [ACTION] [DATABASE_ID] [OPTIONS]

Actions:
  backup [DATABASE_ID] [FULL|INCREMENTAL]  - Create database backup
  scale [DATABASE_ID] [SIZE_GB]           - Scale database storage
  configure [DATABASE_ID]                 - Apply configuration parameters
  monitor [DATABASE_ID] [MINUTES]         - Monitor database performance
  list                                    - List databases in compartment

Environment Variables:
  COMPARTMENT_ID        - OCI Compartment ID (required)
  DRY_RUN              - Set to 'true' for dry run mode
  NOTIFICATION_TOPIC_ID - OCI Notifications Topic ID (optional)

Examples:
  $0 list
  $0 backup ocid1.database.oc1.iad.xxx FULL
  $0 scale ocid1.database.oc1.iad.xxx 500
  $0 monitor ocid1.database.oc1.iad.xxx 30
  COMPARTMENT_ID=ocid1.compartment.oc1..xxx $0 configure ocid1.database.oc1.iad.xxx

EOF
}

# Main execution
main() {
    log "Starting OCI Database Management Script"
    log "Action: ${ACTION}, Database ID: ${DATABASE_ID}"
    
    check_prerequisites
    
    case "${ACTION}" in
        "backup")
            if [[ -z "${DATABASE_ID}" ]]; then
                error_exit "Database ID is required for backup action."
            fi
            local backup_type="${3:-INCREMENTAL}"
            create_backup "${DATABASE_ID}" "${backup_type}"
            ;;
        "scale")
            if [[ -z "${DATABASE_ID}" ]]; then
                error_exit "Database ID is required for scale action."
            fi
            local new_size="${3:-}"
            if [[ -z "${new_size}" ]]; then
                error_exit "New storage size (in GB) is required for scale action."
            fi
            scale_database_storage "${DATABASE_ID}" "${new_size}"
            ;;
        "configure")
            if [[ -z "${DATABASE_ID}" ]]; then
                error_exit "Database ID is required for configure action."
            fi
            configure_database "${DATABASE_ID}"
            ;;
        "monitor")
            if [[ -z "${DATABASE_ID}" ]]; then
                error_exit "Database ID is required for monitor action."
            fi
            local duration="${3:-60}"
            monitor_database "${DATABASE_ID}" "${duration}"
            ;;
        "list")
            list_databases
            ;;
        "help"|*)
            show_usage
            exit 0
            ;;
    esac
    
    log "OCI Database Management Script completed successfully"
}

# Execute main function
main "$@" 