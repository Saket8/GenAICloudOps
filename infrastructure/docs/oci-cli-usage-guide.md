# OCI CLI Scripts Usage Guide

This guide provides comprehensive documentation for using the OCI CLI automation scripts for common remediation scenarios.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Script Categories](#script-categories)
4. [Usage Examples](#usage-examples)
5. [Configuration](#configuration)
6. [Scheduling](#scheduling)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Overview

The OCI CLI scripts provide automated solutions for:
- Compute instance scaling
- Database management and backup
- Monitoring and alerting setup
- Cost optimization
- Backup and restore operations
- Security hardening

All scripts follow consistent patterns for logging, error handling, and dry-run capabilities.

## Prerequisites

### Required Software
- OCI CLI (version 3.0+)
- jq (JSON processor)
- bash (version 4.0+)
- bc (basic calculator) - for some scripts

### Installation

```bash
# Install OCI CLI
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Install jq
sudo apt-get install jq  # Ubuntu/Debian
sudo yum install jq     # RHEL/CentOS
brew install jq         # macOS

# Configure OCI CLI
oci setup config
```

### Authentication Setup

1. **API Key Authentication**
   ```bash
   oci setup config
   ```

2. **Instance Principal** (for running on OCI instances)
   ```bash
   oci setup instance-principal
   ```

3. **Resource Principal** (for functions and other services)
   ```bash
   export OCI_RESOURCE_PRINCIPAL_VERSION=2.2
   ```

### Required Environment Variables

```bash
export COMPARTMENT_ID="ocid1.compartment.oc1..aaaaaaaa..."
export NOTIFICATION_TOPIC_ID="ocid1.onstopic.oc1..aaaaaaaa..."  # Optional
export DRY_RUN="true"  # Set to false for actual execution
```

## Script Categories

### 1. Compute Management

#### Instance Scaling (`compute/scale-instances.sh`)

**Purpose**: Automated scaling of compute instances based on metrics or manual triggers.

**Basic Usage**:
```bash
# List available instance pools
./scale-instances.sh list

# Auto-scale based on metrics
./scale-instances.sh auto ocid1.instancepool.oc1.iad.xxx

# Manual scale up
./scale-instances.sh scale-up ocid1.instancepool.oc1.iad.xxx

# Manual scale down
./scale-instances.sh scale-down ocid1.instancepool.oc1.iad.xxx
```

**Configuration File** (`config/scaling-config.json`):
```json
{
  "scale_out_threshold": 80,
  "scale_in_threshold": 30,
  "scale_step": 2,
  "min_size": 1,
  "max_size": 10,
  "cooldown_minutes": 5
}
```

**Examples**:
```bash
# Production auto-scaling with custom thresholds
COMPARTMENT_ID=ocid1.compartment.oc1..xxx \
./scale-instances.sh auto ocid1.instancepool.oc1.iad.xxx

# Development manual scaling
DRY_RUN=false \
./scale-instances.sh scale-up ocid1.instancepool.oc1.iad.xxx

# Emergency scale-down
COMPARTMENT_ID=ocid1.compartment.oc1..xxx \
DRY_RUN=false \
./scale-instances.sh scale-down ocid1.instancepool.oc1.iad.xxx
```

### 2. Database Management

#### Database Operations (`database/manage-database.sh`)

**Purpose**: Automated database operations including backup, scaling, and configuration.

**Basic Usage**:
```bash
# List databases
./manage-database.sh list

# Create backup
./manage-database.sh backup ocid1.database.oc1.iad.xxx FULL

# Scale database storage
./manage-database.sh scale ocid1.database.oc1.iad.xxx 500

# Monitor performance
./manage-database.sh monitor ocid1.database.oc1.iad.xxx 60

# Apply configuration
./manage-database.sh configure ocid1.database.oc1.iad.xxx
```

**Configuration File** (`config/database-config.json`):
```json
{
  "parameters": {
    "cpu_core_count": 4,
    "data_storage_size_in_tbs": 2,
    "auto_scaling_enabled": true
  },
  "backup_policy": {
    "retention_days": 30,
    "backup_type": "INCREMENTAL"
  }
}
```

**Examples**:
```bash
# Production database backup
COMPARTMENT_ID=ocid1.compartment.oc1..xxx \
DRY_RUN=false \
./manage-database.sh backup ocid1.database.oc1.iad.xxx FULL

# Scale database for increased load
./manage-database.sh scale ocid1.database.oc1.iad.xxx 1000

# Monitor database performance for 2 hours
./manage-database.sh monitor ocid1.database.oc1.iad.xxx 120
```

### 3. Monitoring and Alerting

#### Monitoring Setup (`monitoring/setup-monitoring.sh`)

**Purpose**: Automated setup of monitoring metrics, alarms, and notifications.

**Basic Usage**:
```bash
# Create default configuration
./setup-monitoring.sh init

# Setup monitoring
./setup-monitoring.sh create ./monitoring-config.json

# List existing resources
./setup-monitoring.sh list

# Update configuration
./setup-monitoring.sh update ./monitoring-config.json

# Clean up monitoring resources
./setup-monitoring.sh delete
```

**Configuration File** (`config/monitoring-config.json`):
```json
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
      "namespace": "oci_computeagent",
      "query": "CpuUtilization[1m].mean() > 80",
      "severity": "CRITICAL",
      "pending_duration": "PT5M"
    }
  ]
}
```

**Examples**:
```bash
# Initial setup with email notifications
./setup-monitoring.sh init
# Edit the generated config file with your email
./setup-monitoring.sh create

# Production monitoring setup
COMPARTMENT_ID=ocid1.compartment.oc1..xxx \
DRY_RUN=false \
./setup-monitoring.sh create ./prod-monitoring-config.json

# List all monitoring resources
./setup-monitoring.sh list
```

### 4. Cost Optimization

#### Cost Optimizer (`utilities/cost-optimizer.sh`)

**Purpose**: Automated cost optimization including rightsizing and unused resource cleanup.

**Basic Usage**:
```bash
# Analyze resources for optimization
./cost-optimizer.sh analyze

# Generate cost report
./cost-optimizer.sh report

# Perform optimizations (with dry-run)
./cost-optimizer.sh optimize

# Schedule automated optimization
./cost-optimizer.sh schedule
```

**Examples**:
```bash
# Weekly cost analysis
COMPARTMENT_ID=ocid1.compartment.oc1..xxx \
./cost-optimizer.sh analyze

# Monthly cleanup (actual execution)
COMPARTMENT_ID=ocid1.compartment.oc1..xxx \
DRY_RUN=false \
OPTIMIZATION_THRESHOLD=60 \
./cost-optimizer.sh optimize

# Setup automated cost optimization
./cost-optimizer.sh schedule
```

### 5. Backup and Restore

#### Backup Operations (`utilities/backup-restore.sh`)

**Purpose**: Automated backup and restore operations for compute, storage, and databases.

**Basic Usage**:
```bash
# List backups
./backup-restore.sh list volume

# Create instance backup
./backup-restore.sh backup instance ocid1.instance.oc1.iad.xxx

# Create volume backup
./backup-restore.sh backup volume ocid1.volume.oc1.iad.xxx

# Restore instance
./backup-restore.sh restore instance ocid1.image.oc1.iad.xxx subnet-ocid

# Schedule automated backups
./backup-restore.sh schedule
```

**Configuration File** (`config/backup-config.json`):
```json
{
  "backup_policies": {
    "daily": {
      "retention_days": 7,
      "schedule": "0 2 * * *"
    },
    "weekly": {
      "retention_days": 30,
      "schedule": "0 3 * * 0"
    }
  },
  "resource_defaults": {
    "instance": {
      "policy": "daily",
      "include_boot_volume": true
    }
  }
}
```

**Examples**:
```bash
# Production backup
COMPARTMENT_ID=ocid1.compartment.oc1..xxx \
DRY_RUN=false \
./backup-restore.sh backup instance ocid1.instance.oc1.iad.xxx

# Emergency restore
./backup-restore.sh restore instance ocid1.image.oc1.iad.xxx ocid1.subnet.oc1.iad.xxx

# Schedule daily backups
./backup-restore.sh schedule
```

### 6. Security Hardening

#### Security Audit (`utilities/security-hardening.sh`)

**Purpose**: Automated security hardening and audit for OCI resources.

**Basic Usage**:
```bash
# Perform security audit
./security-hardening.sh audit

# Generate security report
./security-hardening.sh report

# Apply security hardening
./security-hardening.sh harden

# Configure security policies
./security-hardening.sh configure
```

**Examples**:
```bash
# Monthly security audit
COMPARTMENT_ID=ocid1.compartment.oc1..xxx \
./security-hardening.sh audit

# Apply security hardening (dry-run first)
COMPARTMENT_ID=ocid1.compartment.oc1..xxx \
DRY_RUN=true \
./security-hardening.sh harden

# Production hardening (actual execution)
COMPARTMENT_ID=ocid1.compartment.oc1..xxx \
DRY_RUN=false \
./security-hardening.sh harden
```

## Configuration

### Global Configuration

Create a global configuration file at `config/global-config.json`:

```json
{
  "default_compartment_id": "ocid1.compartment.oc1..aaaaaaaa...",
  "default_region": "us-ashburn-1",
  "notification_topic_id": "ocid1.onstopic.oc1..aaaaaaaa...",
  "logging": {
    "level": "INFO",
    "file": "/var/log/oci-automation.log"
  },
  "defaults": {
    "dry_run": true,
    "timeout_seconds": 3600,
    "retry_count": 3
  }
}
```

### Environment-Specific Configuration

```bash
# Development environment
export COMPARTMENT_ID="ocid1.compartment.oc1..dev..."
export DRY_RUN="true"
export OPTIMIZATION_THRESHOLD="7"

# Production environment
export COMPARTMENT_ID="ocid1.compartment.oc1..prod..."
export DRY_RUN="false"
export OPTIMIZATION_THRESHOLD="30"
export NOTIFICATION_TOPIC_ID="ocid1.onstopic.oc1..prod..."
```

## Scheduling

### Cron Jobs

```bash
# Edit crontab
crontab -e

# Add automation schedules
# Daily backup at 2 AM
0 2 * * * COMPARTMENT_ID=ocid1.compartment.oc1..xxx /path/to/backup-restore.sh backup-all daily

# Weekly cost analysis on Sundays at 3 AM
0 3 * * 0 COMPARTMENT_ID=ocid1.compartment.oc1..xxx /path/to/cost-optimizer.sh analyze

# Monthly security audit on 1st at 4 AM
0 4 1 * * COMPARTMENT_ID=ocid1.compartment.oc1..xxx /path/to/security-hardening.sh audit

# Auto-scaling check every 5 minutes
*/5 * * * * COMPARTMENT_ID=ocid1.compartment.oc1..xxx /path/to/scale-instances.sh auto ocid1.instancepool.oc1.iad.xxx
```

### Systemd Timers

Create systemd service and timer files for more robust scheduling:

```ini
# /etc/systemd/system/oci-backup.service
[Unit]
Description=OCI Backup Service
After=network.target

[Service]
Type=oneshot
User=oci-automation
Environment=COMPARTMENT_ID=ocid1.compartment.oc1..xxx
ExecStart=/opt/oci-scripts/backup-restore.sh backup-all daily
```

```ini
# /etc/systemd/system/oci-backup.timer
[Unit]
Description=Daily OCI Backup
Requires=oci-backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

## Best Practices

### 1. Safety and Testing

- Always use `DRY_RUN=true` for initial testing
- Test scripts in development environment first
- Implement proper error handling and rollback procedures
- Use logging extensively for audit trails

### 2. Security

- Use instance principals when running on OCI instances
- Rotate API keys regularly
- Implement least privilege access policies
- Encrypt sensitive configuration files

### 3. Monitoring and Alerting

- Set up notifications for script execution
- Monitor script execution logs
- Implement health checks for automated processes
- Alert on failed executions

### 4. Resource Management

- Tag resources created by automation
- Implement proper cleanup procedures
- Monitor resource costs
- Use appropriate resource limits

### 5. Error Handling

- Implement retry logic for transient failures
- Use proper exit codes
- Log errors with context
- Implement graceful degradation

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Check OCI configuration
   oci iam user get --user-id $(oci iam user list --query 'data[0].id' --raw-output)
   
   # Verify compartment access
   oci iam compartment get --compartment-id $COMPARTMENT_ID
   ```

2. **Script Not Found**
   ```bash
   # Check script permissions
   chmod +x /path/to/script.sh
   
   # Verify path
   which oci
   echo $PATH
   ```

3. **Configuration Issues**
   ```bash
   # Validate JSON configuration
   jq '.' config/monitoring-config.json
   
   # Check environment variables
   env | grep OCI
   env | grep COMPARTMENT
   ```

4. **Network Connectivity**
   ```bash
   # Test OCI API connectivity
   oci iam region list
   
   # Check DNS resolution
   nslookup identity.us-ashburn-1.oraclecloud.com
   ```

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
# Enable debug logging
export OCI_CLI_DEBUG=1
export TF_LOG=DEBUG

# Run script with verbose output
bash -x ./script-name.sh
```

### Log Analysis

```bash
# Check script logs
tail -f /var/log/oci-automation.log

# Filter for errors
grep -i error /var/log/oci-automation.log

# Check system logs
journalctl -u oci-backup.service
```

### Getting Help

- Check OCI CLI documentation: https://docs.oracle.com/en-us/iaas/tools/oci-cli/
- Review OCI service limits and quotas
- Use OCI Support for service-specific issues
- Check script comments for usage examples

For script-specific issues, check the individual script help:
```bash
./script-name.sh help
``` 