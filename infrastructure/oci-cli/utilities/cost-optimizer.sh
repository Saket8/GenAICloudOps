#!/bin/bash

# OCI CLI Script: Cost Optimization Automation
# Description: Automated cost optimization including rightsizing, unused resource cleanup
# Usage: ./cost-optimizer.sh [analyze|optimize|schedule|report]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/oci-cost-optimizer.log"
REPORT_DIR="${SCRIPT_DIR}/../reports"

# Default values
ACTION="${1:-analyze}"
COMPARTMENT_ID="${COMPARTMENT_ID:-}"
DRY_RUN="${DRY_RUN:-true}"
OPTIMIZATION_THRESHOLD="${OPTIMIZATION_THRESHOLD:-30}"  # Days for unused resources

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
        error_exit "jq command not found."
    fi
    
    if [[ -z "${COMPARTMENT_ID}" ]]; then
        error_exit "COMPARTMENT_ID environment variable is required."
    fi
    
    mkdir -p "${REPORT_DIR}"
    
    log "Prerequisites check completed."
}

# Analyze compute instance utilization
analyze_compute_instances() {
    log "Analyzing compute instance utilization..."
    
    local instances
    instances=$(oci compute instance list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state RUNNING \
        --query 'data[].{id:id,name:"display-name",shape:shape,state:"lifecycle-state"}' \
        --output json)
    
    local report_file="${REPORT_DIR}/compute-analysis-$(date +%Y%m%d).json"
    local optimization_suggestions=()
    
    echo "${instances}" | jq -r '.[] | @base64' | while IFS= read -r instance_data; do
        local instance
        instance=$(echo "${instance_data}" | base64 --decode)
        
        local instance_id
        local instance_name
        local shape
        
        instance_id=$(echo "${instance}" | jq -r '.id')
        instance_name=$(echo "${instance}" | jq -r '.name')
        shape=$(echo "${instance}" | jq -r '.shape')
        
        log "Analyzing instance: ${instance_name} (${shape})"
        
        # Get CPU utilization for the last 30 days
        local end_time
        local start_time
        end_time=$(date -u '+%Y-%m-%dT%H:%M:%S.000Z')
        start_time=$(date -u -d '30 days ago' '+%Y-%m-%dT%H:%M:%S.000Z')
        
        local avg_cpu
        avg_cpu=$(oci monitoring metric-data summarize-metrics-data \
            --compartment-id "${COMPARTMENT_ID}" \
            --namespace "oci_computeagent" \
            --query-data '[{
                "query": "CpuUtilization[1h].mean()",
                "startTime": "'${start_time}'",
                "endTime": "'${end_time}'",
                "resolution": "PT1H"
            }]' \
            --query 'data[0]."aggregated-datapoints" | map(.value) | add / length(@)' \
            --raw-output 2>/dev/null || echo "0")
        
        # Determine optimization recommendations
        local recommendation=""
        local potential_savings=""
        
        if (( $(echo "${avg_cpu} < 10" | bc -l) )); then
            recommendation="Consider downsizing or terminating - very low utilization"
            potential_savings="40-60%"
        elif (( $(echo "${avg_cpu} < 25" | bc -l) )); then
            recommendation="Consider downsizing to smaller shape"
            potential_savings="20-40%"
        elif (( $(echo "${avg_cpu} > 80" | bc -l) )); then
            recommendation="Consider upsizing for better performance"
            potential_savings="Performance gain"
        else
            recommendation="Current sizing appears appropriate"
            potential_savings="N/A"
        fi
        
        # Create optimization record
        local optimization_record
        optimization_record=$(jq -n \
            --arg id "${instance_id}" \
            --arg name "${instance_name}" \
            --arg shape "${shape}" \
            --arg cpu "${avg_cpu}" \
            --arg recommendation "${recommendation}" \
            --arg savings "${potential_savings}" \
            '{
                instance_id: $id,
                instance_name: $name,
                current_shape: $shape,
                avg_cpu_utilization: ($cpu | tonumber),
                recommendation: $recommendation,
                potential_savings: $savings,
                analysis_date: now | strftime("%Y-%m-%d %H:%M:%S")
            }')
        
        echo "${optimization_record}" >> "${report_file}.tmp"
        
        log "  Average CPU: ${avg_cpu}% - ${recommendation}"
    done
    
    # Consolidate report
    if [[ -f "${report_file}.tmp" ]]; then
        jq -s '.' "${report_file}.tmp" > "${report_file}"
        rm "${report_file}.tmp"
        log "Compute analysis report saved to: ${report_file}"
    fi
}

# Analyze storage utilization
analyze_storage() {
    log "Analyzing storage utilization..."
    
    local report_file="${REPORT_DIR}/storage-analysis-$(date +%Y%m%d).json"
    
    # Analyze Block Volumes
    log "Checking block volumes..."
    local volumes
    volumes=$(oci bv volume list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state AVAILABLE \
        --query 'data[].{id:id,name:"display-name",size:"size-in-gbs",state:"lifecycle-state"}' \
        --output json)
    
    # Check for unattached volumes
    echo "${volumes}" | jq -r '.[] | @base64' | while IFS= read -r volume_data; do
        local volume
        volume=$(echo "${volume_data}" | base64 --decode)
        
        local volume_id
        local volume_name
        local size_gb
        
        volume_id=$(echo "${volume}" | jq -r '.id')
        volume_name=$(echo "${volume}" | jq -r '.name')
        size_gb=$(echo "${volume}" | jq -r '.size')
        
        # Check if volume is attached
        local attachments
        attachments=$(oci compute volume-attachment list \
            --compartment-id "${COMPARTMENT_ID}" \
            --volume-id "${volume_id}" \
            --query 'data[?"lifecycle-state" == `ATTACHED`]' \
            --output json)
        
        local attachment_count
        attachment_count=$(echo "${attachments}" | jq 'length')
        
        local recommendation=""
        local potential_savings=""
        
        if [[ ${attachment_count} -eq 0 ]]; then
            recommendation="Unattached volume - consider deletion if not needed"
            potential_savings="100% of volume cost"
        else
            recommendation="Volume is in use"
            potential_savings="N/A"
        fi
        
        local storage_record
        storage_record=$(jq -n \
            --arg id "${volume_id}" \
            --arg name "${volume_name}" \
            --arg size "${size_gb}" \
            --arg attached "${attachment_count}" \
            --arg recommendation "${recommendation}" \
            --arg savings "${potential_savings}" \
            '{
                volume_id: $id,
                volume_name: $name,
                size_gb: ($size | tonumber),
                attached_instances: ($attached | tonumber),
                recommendation: $recommendation,
                potential_savings: $savings,
                analysis_date: now | strftime("%Y-%m-%d %H:%M:%S")
            }')
        
        echo "${storage_record}" >> "${report_file}.tmp"
        
        log "  Volume: ${volume_name} (${size_gb}GB) - ${recommendation}"
    done
    
    # Consolidate storage report
    if [[ -f "${report_file}.tmp" ]]; then
        jq -s '.' "${report_file}.tmp" > "${report_file}"
        rm "${report_file}.tmp"
        log "Storage analysis report saved to: ${report_file}"
    fi
}

# Analyze network resources
analyze_network() {
    log "Analyzing network resources..."
    
    local report_file="${REPORT_DIR}/network-analysis-$(date +%Y%m%d).json"
    
    # Check for unused Load Balancers
    log "Checking load balancers..."
    local load_balancers
    load_balancers=$(oci lb load-balancer list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state ACTIVE \
        --query 'data[].{id:id,name:"display-name",shape:"shape-name"}' \
        --output json 2>/dev/null || echo "[]")
    
    echo "${load_balancers}" | jq -r '.[] | @base64' | while IFS= read -r lb_data; do
        local lb
        lb=$(echo "${lb_data}" | base64 --decode)
        
        local lb_id
        local lb_name
        local shape
        
        lb_id=$(echo "${lb}" | jq -r '.id')
        lb_name=$(echo "${lb}" | jq -r '.name')
        shape=$(echo "${lb}" | jq -r '.shape')
        
        # Check backend sets and servers
        local backend_sets
        backend_sets=$(oci lb backend-set list \
            --load-balancer-id "${lb_id}" \
            --query 'data | length' \
            --raw-output 2>/dev/null || echo "0")
        
        local recommendation=""
        local potential_savings=""
        
        if [[ ${backend_sets} -eq 0 ]]; then
            recommendation="Load balancer has no backend sets - consider deletion"
            potential_savings="100% of load balancer cost"
        else
            recommendation="Load balancer is configured with backend sets"
            potential_savings="N/A"
        fi
        
        local network_record
        network_record=$(jq -n \
            --arg id "${lb_id}" \
            --arg name "${lb_name}" \
            --arg shape "${shape}" \
            --arg backends "${backend_sets}" \
            --arg recommendation "${recommendation}" \
            --arg savings "${potential_savings}" \
            '{
                load_balancer_id: $id,
                load_balancer_name: $name,
                shape: $shape,
                backend_sets: ($backends | tonumber),
                recommendation: $recommendation,
                potential_savings: $savings,
                analysis_date: now | strftime("%Y-%m-%d %H:%M:%S")
            }')
        
        echo "${network_record}" >> "${report_file}.tmp"
        
        log "  Load Balancer: ${lb_name} (${shape}) - ${recommendation}"
    done
    
    # Consolidate network report
    if [[ -f "${report_file}.tmp" ]]; then
        jq -s '.' "${report_file}.tmp" > "${report_file}"
        rm "${report_file}.tmp"
        log "Network analysis report saved to: ${report_file}"
    fi
}

# Generate comprehensive cost report
generate_cost_report() {
    log "Generating comprehensive cost optimization report..."
    
    local report_date
    report_date=$(date +%Y%m%d)
    local summary_report="${REPORT_DIR}/cost-optimization-summary-${report_date}.json"
    
    # Collect all analysis files
    local compute_report="${REPORT_DIR}/compute-analysis-${report_date}.json"
    local storage_report="${REPORT_DIR}/storage-analysis-${report_date}.json"
    local network_report="${REPORT_DIR}/network-analysis-${report_date}.json"
    
    # Create summary report
    local summary
    summary=$(jq -n \
        --arg date "${report_date}" \
        --argjson compute "$(cat "${compute_report}" 2>/dev/null || echo '[]')" \
        --argjson storage "$(cat "${storage_report}" 2>/dev/null || echo '[]')" \
        --argjson network "$(cat "${network_report}" 2>/dev/null || echo '[]')" \
        '{
            report_date: $date,
            summary: {
                total_compute_instances: ($compute | length),
                underutilized_instances: ($compute | map(select(.avg_cpu_utilization < 25)) | length),
                unattached_volumes: ($storage | map(select(.attached_instances == 0)) | length),
                unused_load_balancers: ($network | map(select(.backend_sets == 0)) | length)
            },
            recommendations: {
                compute: $compute,
                storage: $storage,
                network: $network
            },
            generated_at: now | strftime("%Y-%m-%d %H:%M:%S")
        }')
    
    echo "${summary}" > "${summary_report}"
    
    log "Cost optimization summary report saved to: ${summary_report}"
    
    # Display summary
    echo ""
    echo "=== Cost Optimization Summary ==="
    jq -r '.summary | to_entries[] | "\(.key): \(.value)"' "${summary_report}"
    echo ""
}

# Perform automated optimizations
perform_optimizations() {
    log "Performing automated cost optimizations..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN mode: No actual changes will be made"
    fi
    
    # Clean up unattached volumes older than threshold
    log "Checking for unattached volumes older than ${OPTIMIZATION_THRESHOLD} days..."
    
    local volumes
    volumes=$(oci bv volume list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state AVAILABLE \
        --query 'data[]' \
        --output json)
    
    echo "${volumes}" | jq -r '.[] | @base64' | while IFS= read -r volume_data; do
        local volume
        volume=$(echo "${volume_data}" | base64 --decode)
        
        local volume_id
        local volume_name
        local time_created
        
        volume_id=$(echo "${volume}" | jq -r '.id')
        volume_name=$(echo "${volume}" | jq -r '."display-name"')
        time_created=$(echo "${volume}" | jq -r '."time-created"')
        
        # Check if volume is attached
        local attachments
        attachments=$(oci compute volume-attachment list \
            --compartment-id "${COMPARTMENT_ID}" \
            --volume-id "${volume_id}" \
            --query 'data[?"lifecycle-state" == `ATTACHED`]' \
            --output json)
        
        local attachment_count
        attachment_count=$(echo "${attachments}" | jq 'length')
        
        if [[ ${attachment_count} -eq 0 ]]; then
            # Calculate age in days
            local created_timestamp
            local current_timestamp
            local age_days
            
            created_timestamp=$(date -d "${time_created}" +%s)
            current_timestamp=$(date +%s)
            age_days=$(( (current_timestamp - created_timestamp) / 86400 ))
            
            if [[ ${age_days} -gt ${OPTIMIZATION_THRESHOLD} ]]; then
                log "Found unattached volume older than ${OPTIMIZATION_THRESHOLD} days: ${volume_name} (${age_days} days old)"
                
                if [[ "${DRY_RUN}" == "true" ]]; then
                    log "DRY RUN: Would delete volume ${volume_name}"
                else
                    log "Deleting unattached volume: ${volume_name}"
                    oci bv volume delete \
                        --volume-id "${volume_id}" \
                        --force \
                        --wait-for-state TERMINATED \
                        --max-wait-seconds 300
                    
                    if [[ $? -eq 0 ]]; then
                        log "Successfully deleted volume: ${volume_name}"
                    else
                        log "Failed to delete volume: ${volume_name}"
                    fi
                fi
            fi
        fi
    done
}

# Schedule cost optimization
schedule_optimization() {
    log "Setting up scheduled cost optimization..."
    
    local cron_file="/tmp/oci-cost-optimizer-cron"
    local script_path="${SCRIPT_DIR}/cost-optimizer.sh"
    
    # Create cron job for weekly analysis
    cat > "${cron_file}" << EOF
# OCI Cost Optimization - Weekly Analysis (Sundays at 2 AM)
0 2 * * 0 COMPARTMENT_ID=${COMPARTMENT_ID} ${script_path} analyze >> ${LOG_FILE} 2>&1

# OCI Cost Optimization - Monthly Cleanup (1st of month at 3 AM)
0 3 1 * * COMPARTMENT_ID=${COMPARTMENT_ID} DRY_RUN=false ${script_path} optimize >> ${LOG_FILE} 2>&1
EOF
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would install cron job:"
        cat "${cron_file}"
    else
        crontab "${cron_file}"
        log "Cron job installed for automated cost optimization"
    fi
    
    rm -f "${cron_file}"
}

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [ACTION]

Actions:
  analyze    - Analyze resources for cost optimization opportunities
  optimize   - Perform automated cost optimizations
  report     - Generate comprehensive cost optimization report
  schedule   - Set up scheduled cost optimization
  help       - Show this help message

Environment Variables:
  COMPARTMENT_ID            - OCI Compartment ID (required)
  DRY_RUN                  - Set to 'false' to perform actual changes (default: true)
  OPTIMIZATION_THRESHOLD   - Days threshold for unused resource cleanup (default: 30)

Examples:
  $0 analyze
  $0 report  
  COMPARTMENT_ID=ocid1.compartment.oc1..xxx DRY_RUN=false $0 optimize
  OPTIMIZATION_THRESHOLD=60 $0 analyze

Reports are saved to: ${REPORT_DIR}

EOF
}

# Main execution
main() {
    log "Starting OCI Cost Optimization Script"
    log "Action: ${ACTION}, Dry Run: ${DRY_RUN}"
    
    check_prerequisites
    
    case "${ACTION}" in
        "analyze")
            analyze_compute_instances
            analyze_storage
            analyze_network
            generate_cost_report
            ;;
        "optimize")
            perform_optimizations
            ;;
        "report")
            generate_cost_report
            ;;
        "schedule")
            schedule_optimization
            ;;
        "help"|*)
            show_usage
            exit 0
            ;;
    esac
    
    log "OCI Cost Optimization Script completed successfully"
}

# Execute main function
main "$@" 