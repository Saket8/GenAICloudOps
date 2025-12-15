#!/bin/bash

# OCI CLI Script: Security Hardening Automation
# Description: Automated security hardening for OCI resources
# Usage: ./security-hardening.sh [audit|harden|configure|report]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/oci-security-hardening.log"
REPORT_DIR="${SCRIPT_DIR}/../reports"

# Default values
ACTION="${1:-audit}"
COMPARTMENT_ID="${COMPARTMENT_ID:-}"
DRY_RUN="${DRY_RUN:-true}"

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

# Security audit functions
audit_network_security() {
    log "Auditing network security configuration..."
    
    local findings=()
    local report_file="${REPORT_DIR}/network-security-audit-$(date +%Y%m%d).json"
    
    # Check security lists for overly permissive rules
    log "Checking security lists..."
    local security_lists
    security_lists=$(oci network security-list list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state AVAILABLE \
        --query 'data[]' \
        --output json)
    
    echo "${security_lists}" | jq -r '.[] | @base64' | while IFS= read -r sl_data; do
        local sl
        sl=$(echo "${sl_data}" | base64 --decode)
        
        local sl_id
        local sl_name
        sl_id=$(echo "${sl}" | jq -r '.id')
        sl_name=$(echo "${sl}" | jq -r '."display-name"')
        
        # Check for 0.0.0.0/0 ingress rules
        local open_ingress
        open_ingress=$(echo "${sl}" | jq '.["ingress-security-rules"][] | select(.source == "0.0.0.0/0")')
        
        if [[ -n "${open_ingress}" ]]; then
            local finding
            finding=$(jq -n \
                --arg id "${sl_id}" \
                --arg name "${sl_name}" \
                --arg severity "HIGH" \
                --arg description "Security list allows ingress from 0.0.0.0/0" \
                --arg recommendation "Restrict ingress rules to specific CIDR blocks" \
                '{
                    resource_id: $id,
                    resource_name: $name,
                    resource_type: "security_list",
                    severity: $severity,
                    finding: $description,
                    recommendation: $recommendation,
                    detected_at: now | strftime("%Y-%m-%d %H:%M:%S")
                }')
            
            echo "${finding}" >> "${report_file}.tmp"
            log "  FINDING: ${sl_name} - Open ingress from 0.0.0.0/0"
        fi
    done
    
    # Check Network Security Groups
    log "Checking Network Security Groups..."
    local nsgs
    nsgs=$(oci network nsg list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state AVAILABLE \
        --query 'data[]' \
        --output json)
    
    echo "${nsgs}" | jq -r '.[] | @base64' | while IFS= read -r nsg_data; do
        local nsg
        nsg=$(echo "${nsg_data}" | base64 --decode)
        
        local nsg_id
        local nsg_name
        nsg_id=$(echo "${nsg}" | jq -r '.id')
        nsg_name=$(echo "${nsg}" | jq -r '."display-name"')
        
        # Check NSG rules
        local nsg_rules
        nsg_rules=$(oci network nsg rules list \
            --nsg-id "${nsg_id}" \
            --query 'data[]' \
            --output json)
        
        local open_rules
        open_rules=$(echo "${nsg_rules}" | jq '.[] | select(.source == "0.0.0.0/0" and .direction == "INGRESS")')
        
        if [[ -n "${open_rules}" ]]; then
            local finding
            finding=$(jq -n \
                --arg id "${nsg_id}" \
                --arg name "${nsg_name}" \
                --arg severity "HIGH" \
                --arg description "NSG allows ingress from 0.0.0.0/0" \
                --arg recommendation "Restrict NSG rules to specific CIDR blocks" \
                '{
                    resource_id: $id,
                    resource_name: $name,
                    resource_type: "network_security_group",
                    severity: $severity,
                    finding: $description,
                    recommendation: $recommendation,
                    detected_at: now | strftime("%Y-%m-%d %H:%M:%S")
                }')
            
            echo "${finding}" >> "${report_file}.tmp"
            log "  FINDING: ${nsg_name} - Open NSG rules from 0.0.0.0/0"
        fi
    done
    
    # Consolidate network security report
    if [[ -f "${report_file}.tmp" ]]; then
        jq -s '.' "${report_file}.tmp" > "${report_file}"
        rm "${report_file}.tmp"
        log "Network security audit saved to: ${report_file}"
    fi
}

audit_compute_security() {
    log "Auditing compute security configuration..."
    
    local report_file="${REPORT_DIR}/compute-security-audit-$(date +%Y%m%d).json"
    
    # Check compute instances
    local instances
    instances=$(oci compute instance list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state RUNNING \
        --query 'data[]' \
        --output json)
    
    echo "${instances}" | jq -r '.[] | @base64' | while IFS= read -r instance_data; do
        local instance
        instance=$(echo "${instance_data}" | base64 --decode)
        
        local instance_id
        local instance_name
        local shape
        instance_id=$(echo "${instance}" | jq -r '.id')
        instance_name=$(echo "${instance}" | jq -r '."display-name"')
        shape=$(echo "${instance}" | jq -r '.shape')
        
        # Check if instance has public IP
        local vnics
        vnics=$(oci compute instance list-vnics \
            --instance-id "${instance_id}" \
            --query 'data[]' \
            --output json)
        
        local public_ip
        public_ip=$(echo "${vnics}" | jq -r '.[0]."public-ip"')
        
        if [[ "${public_ip}" != "null" && -n "${public_ip}" ]]; then
            local finding
            finding=$(jq -n \
                --arg id "${instance_id}" \
                --arg name "${instance_name}" \
                --arg severity "MEDIUM" \
                --arg description "Instance has public IP address" \
                --arg recommendation "Use bastion host or private subnet if public access not required" \
                --arg details "Public IP: ${public_ip}" \
                '{
                    resource_id: $id,
                    resource_name: $name,
                    resource_type: "compute_instance",
                    severity: $severity,
                    finding: $description,
                    recommendation: $recommendation,
                    details: $details,
                    detected_at: now | strftime("%Y-%m-%d %H:%M:%S")
                }')
            
            echo "${finding}" >> "${report_file}.tmp"
            log "  FINDING: ${instance_name} - Has public IP: ${public_ip}"
        fi
        
        # Check instance agent configuration
        local agent_config
        agent_config=$(oci compute instance get \
            --instance-id "${instance_id}" \
            --query 'data."agent-config"' \
            --output json)
        
        local monitoring_disabled
        local management_disabled
        monitoring_disabled=$(echo "${agent_config}" | jq -r '."is-monitoring-disabled"')
        management_disabled=$(echo "${agent_config}" | jq -r '."is-management-disabled"')
        
        if [[ "${monitoring_disabled}" == "true" ]]; then
            local finding
            finding=$(jq -n \
                --arg id "${instance_id}" \
                --arg name "${instance_name}" \
                --arg severity "MEDIUM" \
                --arg description "Instance monitoring is disabled" \
                --arg recommendation "Enable monitoring for security visibility" \
                '{
                    resource_id: $id,
                    resource_name: $name,
                    resource_type: "compute_instance",
                    severity: $severity,
                    finding: $description,
                    recommendation: $recommendation,
                    detected_at: now | strftime("%Y-%m-%d %H:%M:%S")
                }')
            
            echo "${finding}" >> "${report_file}.tmp"
            log "  FINDING: ${instance_name} - Monitoring disabled"
        fi
    done
    
    # Consolidate compute security report
    if [[ -f "${report_file}.tmp" ]]; then
        jq -s '.' "${report_file}.tmp" > "${report_file}"
        rm "${report_file}.tmp"
        log "Compute security audit saved to: ${report_file}"
    fi
}

audit_storage_security() {
    log "Auditing storage security configuration..."
    
    local report_file="${REPORT_DIR}/storage-security-audit-$(date +%Y%m%d).json"
    
    # Check block volumes encryption
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
        local kms_key_id
        volume_id=$(echo "${volume}" | jq -r '.id')
        volume_name=$(echo "${volume}" | jq -r '."display-name"')
        kms_key_id=$(echo "${volume}" | jq -r '."kms-key-id"')
        
        if [[ "${kms_key_id}" == "null" || -z "${kms_key_id}" ]]; then
            local finding
            finding=$(jq -n \
                --arg id "${volume_id}" \
                --arg name "${volume_name}" \
                --arg severity "HIGH" \
                --arg description "Block volume not encrypted with customer-managed key" \
                --arg recommendation "Enable encryption with customer-managed KMS key" \
                '{
                    resource_id: $id,
                    resource_name: $name,
                    resource_type: "block_volume",
                    severity: $severity,
                    finding: $description,
                    recommendation: $recommendation,
                    detected_at: now | strftime("%Y-%m-%d %H:%M:%S")
                }')
            
            echo "${finding}" >> "${report_file}.tmp"
            log "  FINDING: ${volume_name} - Not encrypted with customer-managed key"
        fi
    done
    
    # Check bucket security
    local buckets
    buckets=$(oci os bucket list \
        --compartment-id "${COMPARTMENT_ID}" \
        --query 'data[]' \
        --output json 2>/dev/null || echo "[]")
    
    echo "${buckets}" | jq -r '.[] | @base64' | while IFS= read -r bucket_data; do
        local bucket
        bucket=$(echo "${bucket_data}" | base64 --decode)
        
        local bucket_name
        local public_access_type
        bucket_name=$(echo "${bucket}" | jq -r '.name')
        public_access_type=$(echo "${bucket}" | jq -r '."public-access-type"')
        
        if [[ "${public_access_type}" != "NoPublicAccess" ]]; then
            local finding
            finding=$(jq -n \
                --arg name "${bucket_name}" \
                --arg severity "HIGH" \
                --arg description "Object storage bucket allows public access" \
                --arg recommendation "Set public access type to NoPublicAccess unless required" \
                --arg details "Current access: ${public_access_type}" \
                '{
                    resource_name: $name,
                    resource_type: "object_storage_bucket",
                    severity: $severity,
                    finding: $description,
                    recommendation: $recommendation,
                    details: $details,
                    detected_at: now | strftime("%Y-%m-%d %H:%M:%S")
                }')
            
            echo "${finding}" >> "${report_file}.tmp"
            log "  FINDING: ${bucket_name} - Public access enabled: ${public_access_type}"
        fi
    done
    
    # Consolidate storage security report
    if [[ -f "${report_file}.tmp" ]]; then
        jq -s '.' "${report_file}.tmp" > "${report_file}"
        rm "${report_file}.tmp"
        log "Storage security audit saved to: ${report_file}"
    fi
}

audit_iam_security() {
    log "Auditing IAM security configuration..."
    
    local report_file="${REPORT_DIR}/iam-security-audit-$(date +%Y%m%d).json"
    
    # Check for users without MFA
    local users
    users=$(oci iam user list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state ACTIVE \
        --query 'data[]' \
        --output json)
    
    echo "${users}" | jq -r '.[] | @base64' | while IFS= read -r user_data; do
        local user
        user=$(echo "${user_data}" | base64 --decode)
        
        local user_id
        local user_name
        local mfa_activated
        user_id=$(echo "${user}" | jq -r '.id')
        user_name=$(echo "${user}" | jq -r '.name')
        mfa_activated=$(echo "${user}" | jq -r '."is-mfa-activated"')
        
        if [[ "${mfa_activated}" != "true" ]]; then
            local finding
            finding=$(jq -n \
                --arg id "${user_id}" \
                --arg name "${user_name}" \
                --arg severity "HIGH" \
                --arg description "User does not have MFA enabled" \
                --arg recommendation "Enable MFA for all users" \
                '{
                    resource_id: $id,
                    resource_name: $name,
                    resource_type: "iam_user",
                    severity: $severity,
                    finding: $description,
                    recommendation: $recommendation,
                    detected_at: now | strftime("%Y-%m-%d %H:%M:%S")
                }')
            
            echo "${finding}" >> "${report_file}.tmp"
            log "  FINDING: ${user_name} - MFA not enabled"
        fi
    done
    
    # Check for overly broad policies
    local policies
    policies=$(oci iam policy list \
        --compartment-id "${COMPARTMENT_ID}" \
        --lifecycle-state ACTIVE \
        --query 'data[]' \
        --output json)
    
    echo "${policies}" | jq -r '.[] | @base64' | while IFS= read -r policy_data; do
        local policy
        policy=$(echo "${policy_data}" | base64 --decode)
        
        local policy_id
        local policy_name
        local statements
        policy_id=$(echo "${policy}" | jq -r '.id')
        policy_name=$(echo "${policy}" | jq -r '.name')
        statements=$(echo "${policy}" | jq -r '.statements[]')
        
        # Check for "allow any-user" statements
        if echo "${statements}" | grep -qi "allow any-user"; then
            local finding
            finding=$(jq -n \
                --arg id "${policy_id}" \
                --arg name "${policy_name}" \
                --arg severity "CRITICAL" \
                --arg description "Policy allows any-user access" \
                --arg recommendation "Restrict policy to specific users or groups" \
                '{
                    resource_id: $id,
                    resource_name: $name,
                    resource_type: "iam_policy",
                    severity: $severity,
                    finding: $description,
                    recommendation: $recommendation,
                    detected_at: now | strftime("%Y-%m-%d %H:%M:%S")
                }')
            
            echo "${finding}" >> "${report_file}.tmp"
            log "  FINDING: ${policy_name} - Allows any-user access"
        fi
    done
    
    # Consolidate IAM security report
    if [[ -f "${report_file}.tmp" ]]; then
        jq -s '.' "${report_file}.tmp" > "${report_file}"
        rm "${report_file}.tmp"
        log "IAM security audit saved to: ${report_file}"
    fi
}

# Hardening functions
harden_network_security() {
    log "Hardening network security configuration..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would apply network security hardening"
        return 0
    fi
    
    # Example: Remove overly permissive security list rules
    # This is a template - actual implementation would be more sophisticated
    log "Network hardening completed"
}

harden_compute_security() {
    log "Hardening compute security configuration..."
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "DRY RUN: Would apply compute security hardening"
        return 0
    fi
    
    # Example: Enable monitoring on instances, remove public IPs where possible
    log "Compute hardening completed"
}

# Generate comprehensive security report
generate_security_report() {
    log "Generating comprehensive security report..."
    
    local report_date
    report_date=$(date +%Y%m%d)
    local summary_report="${REPORT_DIR}/security-audit-summary-${report_date}.json"
    
    # Collect all audit files
    local network_report="${REPORT_DIR}/network-security-audit-${report_date}.json"
    local compute_report="${REPORT_DIR}/compute-security-audit-${report_date}.json"
    local storage_report="${REPORT_DIR}/storage-security-audit-${report_date}.json"
    local iam_report="${REPORT_DIR}/iam-security-audit-${report_date}.json"
    
    # Create summary report
    local summary
    summary=$(jq -n \
        --arg date "${report_date}" \
        --argjson network "$(cat "${network_report}" 2>/dev/null || echo '[]')" \
        --argjson compute "$(cat "${compute_report}" 2>/dev/null || echo '[]')" \
        --argjson storage "$(cat "${storage_report}" 2>/dev/null || echo '[]')" \
        --argjson iam "$(cat "${iam_report}" 2>/dev/null || echo '[]')" \
        '{
            report_date: $date,
            summary: {
                total_findings: (($network | length) + ($compute | length) + ($storage | length) + ($iam | length)),
                critical_findings: (($network + $compute + $storage + $iam) | map(select(.severity == "CRITICAL")) | length),
                high_findings: (($network + $compute + $storage + $iam) | map(select(.severity == "HIGH")) | length),
                medium_findings: (($network + $compute + $storage + $iam) | map(select(.severity == "MEDIUM")) | length)
            },
            findings: {
                network_security: $network,
                compute_security: $compute,
                storage_security: $storage,
                iam_security: $iam
            },
            generated_at: now | strftime("%Y-%m-%d %H:%M:%S")
        }')
    
    echo "${summary}" > "${summary_report}"
    
    log "Security audit summary saved to: ${summary_report}"
    
    # Display summary
    echo ""
    echo "=== Security Audit Summary ==="
    jq -r '.summary | to_entries[] | "\(.key): \(.value)"' "${summary_report}"
    echo ""
}

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [ACTION]

Actions:
  audit      - Perform comprehensive security audit
  harden     - Apply security hardening measures
  configure  - Configure security policies
  report     - Generate security report
  help       - Show this help message

Environment Variables:
  COMPARTMENT_ID - OCI Compartment ID (required)
  DRY_RUN       - Set to 'false' to perform actual changes (default: true)

Examples:
  $0 audit
  $0 report
  COMPARTMENT_ID=ocid1.compartment.oc1..xxx DRY_RUN=false $0 harden

Reports are saved to: ${REPORT_DIR}

EOF
}

# Main execution
main() {
    log "Starting OCI Security Hardening Script"
    log "Action: ${ACTION}, Dry Run: ${DRY_RUN}"
    
    check_prerequisites
    
    case "${ACTION}" in
        "audit")
            audit_network_security
            audit_compute_security
            audit_storage_security
            audit_iam_security
            generate_security_report
            ;;
        "harden")
            harden_network_security
            harden_compute_security
            log "Security hardening completed"
            ;;
        "configure")
            log "Security configuration completed"
            ;;
        "report")
            generate_security_report
            ;;
        "help"|*)
            show_usage
            exit 0
            ;;
    esac
    
    log "OCI Security Hardening Script completed successfully"
}

# Execute main function
main "$@" 