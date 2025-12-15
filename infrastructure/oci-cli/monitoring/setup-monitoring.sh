#!/bin/bash

# OCI CLI Script: Monitoring and Alerting Setup
# Description: Automated setup of monitoring metrics, alarms, and notifications
# Usage: ./setup-monitoring.sh [create|update|delete] [config-file]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/oci-monitoring.log"

# Default values
ACTION="${1:-create}"
CONFIG_FILE="${2:-${SCRIPT_DIR}/../config/monitoring-config.json}"
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
        error_exit "OCI CLI not found."
    fi
    
    if ! command -v jq &> /dev/null; then
        error_exit "jq command not found. Please install jq."
    fi
    
    if [[ -z "${COMPARTMENT_ID}" ]]; then
        error_exit "COMPARTMENT_ID environment variable is required."
    fi
    
    if [[ ! -f "${CONFIG_FILE}" ]] && [[ "${ACTION}" != "delete" ]]; then
        error_exit "Configuration file not found: ${CONFIG_FILE}"
    fi
    
    log "Prerequisites check completed."
}

# Create default monitoring configuration
create_default_config() {
    local config_file="$1"
    
    log "Creating default monitoring configuration at ${config_file}..."
    
    mkdir -p "$(dirname "${config_file}")"
    
    cat > "${config_file}" << 'EOF'
{
  "notification_topics": [
    {
      "name": "genai-cloudops-alerts",
      "description": "GenAI CloudOps Alert Notifications",
      "protocol": "EMAIL",
      "endpoint": "admin@example.com"
    }
  ],
  "alarms": [
    {
      "display_name": "High CPU Utilization",
      "metric_compartment_id": null,
      "namespace": "oci_computeagent",
      "query": "CpuUtilization[1m].mean() > 80",
      "severity": "CRITICAL",
      "pending_duration": "PT5M",
      "resolution": "PT1M",
      "body": "CPU utilization is above 80% for 5 minutes",
      "destinations": [],
      "repeat_notification_duration": "PT30M",
      "suppression": null,
      "is_enabled": true
    },
    {
      "display_name": "High Memory Utilization", 
      "metric_compartment_id": null,
      "namespace": "oci_computeagent",
      "query": "MemoryUtilization[1m].mean() > 85",
      "severity": "WARNING",
      "pending_duration": "PT10M",
      "resolution": "PT1M",
      "body": "Memory utilization is above 85% for 10 minutes",
      "destinations": [],
      "repeat_notification_duration": "PT1H",
      "suppression": null,
      "is_enabled": true
    },
    {
      "display_name": "Disk Space Critical",
      "metric_compartment_id": null,
      "namespace": "oci_computeagent",
      "query": "DiskUtilization[1m].mean() > 90",
      "severity": "CRITICAL",
      "pending_duration": "PT5M",
      "resolution": "PT1M",
      "body": "Disk utilization is above 90% for 5 minutes",
      "destinations": [],
      "repeat_notification_duration": "PT15M",
      "suppression": null,
      "is_enabled": true
    },
    {
      "display_name": "Database CPU High",
      "metric_compartment_id": null,
      "namespace": "oci_autonomous_database",
      "query": "CpuUtilization[5m].mean() > 75",
      "severity": "WARNING",
      "pending_duration": "PT10M",
      "resolution": "PT5M",
      "body": "Database CPU utilization is above 75%",
      "destinations": [],
      "repeat_notification_duration": "PT1H",
      "suppression": null,
      "is_enabled": true
    },
    {
      "display_name": "Load Balancer Health Check Failures",
      "metric_compartment_id": null,
      "namespace": "oci_lbaas",
      "query": "HealthCheckStatus[1m].mean() < 1",
      "severity": "CRITICAL",
      "pending_duration": "PT2M",
      "resolution": "PT1M",
      "body": "Load balancer health check is failing",
      "destinations": [],
      "repeat_notification_duration": "PT10M",
      "suppression": null,
      "is_enabled": true
    }
  ]
}
EOF
    
    log "Default configuration created. Please update ${config_file} with your specific settings."
}

# Create notification topic
create_notification_topic() {
    local topic_config="$1"
    
    local name
    local description
    local protocol
    local endpoint
    
    name=$(echo "${topic_config}" | jq -r '.name')
    description=$(echo "${topic_config}" | jq -r '.description')
    protocol=$(echo "${topic_config}" | jq -r '.protocol')
    endpoint=$(echo "${topic_config}" | jq -r '.endpoint')
    
    log "Creating notification topic: ${name}..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would create notification topic ${name}"
        return 0
    fi
    
    # Create topic
    local topic_id
    topic_id=$(oci ons topic create \
        --compartment-id "${COMPARTMENT_ID}" \
        --name "${name}" \
        --description "${description}" \
        --query 'data.topic-id' \
        --raw-output)
    
    if [[ $? -ne 0 ]]; then
        error_exit "Failed to create notification topic: ${name}"
    fi
    
    log "Created notification topic: ${name} (ID: ${topic_id})"
    
    # Create subscription
    oci ons subscription create \
        --compartment-id "${COMPARTMENT_ID}" \
        --topic-id "${topic_id}" \
        --protocol "${protocol}" \
        --endpoint "${endpoint}" \
        --wait-for-state ACTIVE \
        --max-wait-seconds 300
    
    if [[ $? -eq 0 ]]; then
        log "Created subscription for topic ${name} (${protocol}: ${endpoint})"
    else
        log "WARNING: Failed to create subscription for topic ${name}"
    fi
    
    echo "${topic_id}"
}

# Create alarm
create_alarm() {
    local alarm_config="$1"
    local topic_ids="$2"
    
    local display_name
    local namespace
    local query
    local severity
    local pending_duration
    local resolution
    local body
    local repeat_duration
    local is_enabled
    
    display_name=$(echo "${alarm_config}" | jq -r '.display_name')
    namespace=$(echo "${alarm_config}" | jq -r '.namespace')
    query=$(echo "${alarm_config}" | jq -r '.query')
    severity=$(echo "${alarm_config}" | jq -r '.severity')
    pending_duration=$(echo "${alarm_config}" | jq -r '.pending_duration')
    resolution=$(echo "${alarm_config}" | jq -r '.resolution')
    body=$(echo "${alarm_config}" | jq -r '.body')
    repeat_duration=$(echo "${alarm_config}" | jq -r '.repeat_notification_duration')
    is_enabled=$(echo "${alarm_config}" | jq -r '.is_enabled')
    
    log "Creating alarm: ${display_name}..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would create alarm ${display_name}"
        log "  Query: ${query}"
        log "  Severity: ${severity}"
        return 0
    fi
    
    # Convert topic IDs to array format
    local destinations_json
    destinations_json=$(echo "${topic_ids}" | jq -R 'split(",") | map(select(length > 0))')
    
    # Create alarm
    oci monitoring alarm create \
        --compartment-id "${COMPARTMENT_ID}" \
        --display-name "${display_name}" \
        --metric-compartment-id "${COMPARTMENT_ID}" \
        --namespace "${namespace}" \
        --query "${query}" \
        --severity "${severity}" \
        --pending-duration "${pending_duration}" \
        --resolution "${resolution}" \
        --body "${body}" \
        --destinations "${destinations_json}" \
        --repeat-notification-duration "${repeat_duration}" \
        --is-enabled "${is_enabled}" \
        --wait-for-state ACTIVE \
        --max-wait-seconds 300
    
    if [[ $? -eq 0 ]]; then
        log "Successfully created alarm: ${display_name}"
    else
        error_exit "Failed to create alarm: ${display_name}"
    fi
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring configuration..."
    
    if [[ ! -f "${CONFIG_FILE}" ]]; then
        log "Configuration file not found. Creating default configuration..."
        create_default_config "${CONFIG_FILE}"
        log "Please update the configuration file and run the script again."
        exit 0
    fi
    
    # Read configuration
    local config
    config=$(cat "${CONFIG_FILE}")
    
    # Create notification topics
    local topic_ids=()
    local topics
    topics=$(echo "${config}" | jq -c '.notification_topics[]')
    
    while IFS= read -r topic; do
        if [[ -n "${topic}" ]]; then
            local topic_id
            topic_id=$(create_notification_topic "${topic}")
            topic_ids+=("${topic_id}")
        fi
    done <<< "${topics}"
    
    # Join topic IDs
    local all_topic_ids
    printf -v all_topic_ids '%s,' "${topic_ids[@]}"
    all_topic_ids="${all_topic_ids%,}"
    
    # Create alarms
    local alarms
    alarms=$(echo "${config}" | jq -c '.alarms[]')
    
    while IFS= read -r alarm; do
        if [[ -n "${alarm}" ]]; then
            create_alarm "${alarm}" "${all_topic_ids}"
        fi
    done <<< "${alarms}"
    
    log "Monitoring setup completed successfully!"
}

# List existing monitoring resources
list_monitoring_resources() {
    log "Listing existing monitoring resources..."
    
    echo "=== Notification Topics ==="
    oci ons topic list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state ACTIVE \
        --query 'data[].{name:name,id:"topic-id"}' \
        --output table
    
    echo ""
    echo "=== Alarms ==="
    oci monitoring alarm list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state ACTIVE \
        --query 'data[].{name:"display-name",severity:severity,enabled:"is-enabled"}' \
        --output table
    
    echo ""
    echo "=== Subscriptions ==="
    oci ons subscription list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state ACTIVE \
        --query 'data[].{protocol:protocol,endpoint:endpoint,state:"lifecycle-state"}' \
        --output table
}

# Delete monitoring resources
delete_monitoring() {
    log "Deleting monitoring resources with prefix 'genai-cloudops'..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would delete monitoring resources"
        return 0
    fi
    
    # Delete alarms
    local alarm_ids
    alarm_ids=$(oci monitoring alarm list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state ACTIVE \
        --query 'data[?starts_with("display-name", `genai-cloudops`)].id' \
        --raw-output)
    
    for alarm_id in ${alarm_ids}; do
        if [[ -n "${alarm_id}" ]]; then
            log "Deleting alarm: ${alarm_id}"
            oci monitoring alarm delete --alarm-id "${alarm_id}" --force
        fi
    done
    
    # Delete notification topics
    local topic_ids
    topic_ids=$(oci ons topic list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state ACTIVE \
        --query 'data[?starts_with(name, `genai-cloudops`)].topic-id' \
        --raw-output)
    
    for topic_id in ${topic_ids}; do
        if [[ -n "${topic_id}" ]]; then
            log "Deleting notification topic: ${topic_id}"
            oci ons topic delete --topic-id "${topic_id}" --force
        fi
    done
    
    log "Monitoring resources cleanup completed."
}

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [ACTION] [CONFIG_FILE]

Actions:
  create    - Create monitoring configuration (default)
  update    - Update existing monitoring configuration  
  delete    - Delete monitoring resources
  list      - List existing monitoring resources
  init      - Create default configuration file

Environment Variables:
  COMPARTMENT_ID - OCI Compartment ID (required)
  DRY_RUN       - Set to 'true' for dry run mode

Examples:
  $0 init
  $0 create ./monitoring-config.json
  $0 list
  COMPARTMENT_ID=ocid1.compartment.oc1..xxx $0 create

Configuration file should contain notification topics and alarms in JSON format.
Run '$0 init' to create a template configuration file.

EOF
}

# Main execution
main() {
    log "Starting OCI Monitoring Setup Script"
    log "Action: ${ACTION}, Config File: ${CONFIG_FILE}"
    
    check_prerequisites
    
    case "${ACTION}" in
        "create"|"setup")
            setup_monitoring
            ;;
        "update")
            # For update, we delete and recreate
            log "Updating monitoring configuration..."
            delete_monitoring
            setup_monitoring
            ;;
        "delete"|"cleanup")
            delete_monitoring
            ;;
        "list")
            list_monitoring_resources
            ;;
        "init")
            create_default_config "${CONFIG_FILE}"
            ;;
        "help"|*)
            show_usage
            exit 0
            ;;
    esac
    
    log "OCI Monitoring Setup Script completed successfully"
}

# Execute main function
main "$@" 