#!/bin/bash

# OCI CLI Script: Compute Instance Scaling Automation
# Description: Automated scaling of compute instances based on metrics or manual triggers
# Usage: ./scale-instances.sh [scale-up|scale-down|auto] [instance-pool-id]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../config/scaling-config.json"
LOG_FILE="/var/log/oci-scaling.log"

# Default values
SCALE_ACTION="${1:-auto}"
INSTANCE_POOL_ID="${2:-}"
DRY_RUN="${DRY_RUN:-false}"
COMPARTMENT_ID="${COMPARTMENT_ID:-}"

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
    
    # Check if OCI CLI is installed and configured
    if ! command -v oci &> /dev/null; then
        error_exit "OCI CLI not found. Please install and configure OCI CLI."
    fi
    
    # Verify OCI configuration
    if ! oci iam compartment list --compartment-id-in-subtree true --limit 1 &> /dev/null; then
        error_exit "OCI CLI not properly configured. Please run 'oci setup config'."
    fi
    
    # Check required environment variables
    if [[ -z "${COMPARTMENT_ID}" ]]; then
        error_exit "COMPARTMENT_ID environment variable is required."
    fi
    
    log "Prerequisites check completed successfully."
}

# Get instance pool information
get_instance_pool_info() {
    local pool_id="$1"
    
    log "Retrieving instance pool information for ${pool_id}..."
    
    local pool_info
    pool_info=$(oci compute-management instance-pool get \
        --instance-pool-id "${pool_id}" \
        --query 'data.{size:size,state:"lifecycle-state",displayName:"display-name"}' \
        --output json)
    
    if [[ $? -ne 0 ]]; then
        error_exit "Failed to retrieve instance pool information."
    fi
    
    echo "${pool_info}"
}

# Get CPU utilization metrics
get_cpu_metrics() {
    local pool_id="$1"
    local time_window="${2:-PT5M}"  # 5 minutes by default
    
    log "Retrieving CPU metrics for instance pool ${pool_id}..."
    
    # Get current time and 5 minutes ago
    local end_time
    local start_time
    end_time=$(date -u '+%Y-%m-%dT%H:%M:%S.000Z')
    start_time=$(date -u -d '5 minutes ago' '+%Y-%m-%dT%H:%M:%S.000Z')
    
    # Query CPU utilization metrics
    local cpu_metrics
    cpu_metrics=$(oci monitoring metric-data summarize-metrics-data \
        --compartment-id "${COMPARTMENT_ID}" \
        --namespace "oci_computeagent" \
        --query-data '[{
            "query": "CpuUtilization[5m].mean()",
            "startTime": "'${start_time}'",
            "endTime": "'${end_time}'",
            "resolution": "PT1M"
        }]' \
        --query 'data[0]."aggregated-datapoints"[0].value' \
        --raw-output 2>/dev/null || echo "0")
    
    echo "${cpu_metrics:-0}"
}

# Scale up instance pool
scale_up() {
    local pool_id="$1"
    local target_size="$2"
    
    log "Scaling up instance pool ${pool_id} to ${target_size} instances..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would scale instance pool to ${target_size} instances"
        return 0
    fi
    
    oci compute-management instance-pool update \
        --instance-pool-id "${pool_id}" \
        --size "${target_size}" \
        --force \
        --wait-for-state RUNNING \
        --max-wait-seconds 600
    
    if [[ $? -eq 0 ]]; then
        log "Successfully scaled up instance pool to ${target_size} instances."
        
        # Send notification (if configured)
        send_notification "Scale Up" "Instance pool ${pool_id} scaled up to ${target_size} instances"
    else
        error_exit "Failed to scale up instance pool."
    fi
}

# Scale down instance pool
scale_down() {
    local pool_id="$1"
    local target_size="$2"
    
    log "Scaling down instance pool ${pool_id} to ${target_size} instances..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would scale instance pool to ${target_size} instances"
        return 0
    fi
    
    oci compute-management instance-pool update \
        --instance-pool-id "${pool_id}" \
        --size "${target_size}" \
        --force \
        --wait-for-state RUNNING \
        --max-wait-seconds 600
    
    if [[ $? -eq 0 ]]; then
        log "Successfully scaled down instance pool to ${target_size} instances."
        
        # Send notification (if configured)
        send_notification "Scale Down" "Instance pool ${pool_id} scaled down to ${target_size} instances"
    else
        error_exit "Failed to scale down instance pool."
    fi
}

# Auto-scaling based on metrics
auto_scale() {
    local pool_id="$1"
    
    log "Starting auto-scaling analysis for instance pool ${pool_id}..."
    
    # Get current pool size
    local pool_info
    pool_info=$(get_instance_pool_info "${pool_id}")
    local current_size
    current_size=$(echo "${pool_info}" | jq -r '.size')
    
    # Get CPU metrics
    local cpu_utilization
    cpu_utilization=$(get_cpu_metrics "${pool_id}")
    cpu_utilization=${cpu_utilization%.*}  # Remove decimal part
    
    log "Current pool size: ${current_size}, CPU utilization: ${cpu_utilization}%"
    
    # Load scaling configuration
    local scale_out_threshold=80
    local scale_in_threshold=30
    local scale_step=1
    local min_size=1
    local max_size=10
    
    if [[ -f "${CONFIG_FILE}" ]]; then
        scale_out_threshold=$(jq -r '.scale_out_threshold // 80' "${CONFIG_FILE}")
        scale_in_threshold=$(jq -r '.scale_in_threshold // 30' "${CONFIG_FILE}")
        scale_step=$(jq -r '.scale_step // 1' "${CONFIG_FILE}")
        min_size=$(jq -r '.min_size // 1' "${CONFIG_FILE}")
        max_size=$(jq -r '.max_size // 10' "${CONFIG_FILE}")
    fi
    
    # Make scaling decision
    if [[ ${cpu_utilization} -gt ${scale_out_threshold} ]] && [[ ${current_size} -lt ${max_size} ]]; then
        local new_size=$((current_size + scale_step))
        if [[ ${new_size} -gt ${max_size} ]]; then
            new_size=${max_size}
        fi
        scale_up "${pool_id}" "${new_size}"
    elif [[ ${cpu_utilization} -lt ${scale_in_threshold} ]] && [[ ${current_size} -gt ${min_size} ]]; then
        local new_size=$((current_size - scale_step))
        if [[ ${new_size} -lt ${min_size} ]]; then
            new_size=${min_size}
        fi
        scale_down "${pool_id}" "${new_size}"
    else
        log "No scaling action required. Current metrics within thresholds."
    fi
}

# Send notification (basic implementation)
send_notification() {
    local action="$1"
    local message="$2"
    
    # This is a placeholder for notification system integration
    # You can integrate with OCI Notifications, email, Slack, etc.
    
    log "NOTIFICATION: ${action} - ${message}"
    
    # Example: Send to OCI Notifications Topic (if configured)
    if [[ -n "${NOTIFICATION_TOPIC_ID:-}" ]]; then
        oci ons message publish \
            --topic-id "${NOTIFICATION_TOPIC_ID}" \
            --message "${message}" \
            --title "OCI Auto-Scaling: ${action}" \
            --compartment-id "${COMPARTMENT_ID}" || true
    fi
}

# List available instance pools
list_instance_pools() {
    log "Listing available instance pools in compartment ${COMPARTMENT_ID}..."
    
    oci compute-management instance-pool list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state RUNNING \
        --query 'data[].{id:id,name:"display-name",size:size,state:"lifecycle-state"}' \
        --output table
}

# Main execution
main() {
    log "Starting OCI Instance Scaling Script"
    log "Action: ${SCALE_ACTION}, Instance Pool ID: ${INSTANCE_POOL_ID}"
    
    check_prerequisites
    
    case "${SCALE_ACTION}" in
        "scale-up")
            if [[ -z "${INSTANCE_POOL_ID}" ]]; then
                error_exit "Instance Pool ID is required for scale-up action."
            fi
            # Default scale up by 1
            local pool_info
            pool_info=$(get_instance_pool_info "${INSTANCE_POOL_ID}")
            local current_size
            current_size=$(echo "${pool_info}" | jq -r '.size')
            scale_up "${INSTANCE_POOL_ID}" "$((current_size + 1))"
            ;;
        "scale-down")
            if [[ -z "${INSTANCE_POOL_ID}" ]]; then
                error_exit "Instance Pool ID is required for scale-down action."
            fi
            # Default scale down by 1
            local pool_info
            pool_info=$(get_instance_pool_info "${INSTANCE_POOL_ID}")
            local current_size
            current_size=$(echo "${pool_info}" | jq -r '.size')
            if [[ ${current_size} -gt 1 ]]; then
                scale_down "${INSTANCE_POOL_ID}" "$((current_size - 1))"
            else
                log "Instance pool is already at minimum size (1). No scaling down performed."
            fi
            ;;
        "auto")
            if [[ -z "${INSTANCE_POOL_ID}" ]]; then
                log "No Instance Pool ID provided. Listing available instance pools:"
                list_instance_pools
                exit 0
            fi
            auto_scale "${INSTANCE_POOL_ID}"
            ;;
        "list")
            list_instance_pools
            ;;
        *)
            echo "Usage: $0 [scale-up|scale-down|auto|list] [instance-pool-id]"
            echo ""
            echo "Environment Variables:"
            echo "  COMPARTMENT_ID    - OCI Compartment ID (required)"
            echo "  DRY_RUN          - Set to 'true' for dry run mode"
            echo "  NOTIFICATION_TOPIC_ID - OCI Notifications Topic ID (optional)"
            echo ""
            echo "Examples:"
            echo "  $0 list"
            echo "  $0 auto ocid1.instancepool.oc1.iad.xxx"
            echo "  $0 scale-up ocid1.instancepool.oc1.iad.xxx"
            echo "  COMPARTMENT_ID=ocid1.compartment.oc1..xxx $0 auto"
            exit 1
            ;;
    esac
    
    log "OCI Instance Scaling Script completed successfully"
}

# Execute main function
main "$@" 