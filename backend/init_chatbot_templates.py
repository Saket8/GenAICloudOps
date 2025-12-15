#!/usr/bin/env python3
"""
Initialize default query templates for the chatbot system.
This script creates predefined templates for common cloud operations queries.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db, create_tables
from app.models.chatbot import QueryTemplate
from sqlalchemy.orm import Session
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_TEMPLATES = [
    # Infrastructure Templates
    {
        "name": "Check Instance Status",
        "description": "Check the current status and health of compute instances",
        "category": "Infrastructure",
        "template_text": "What is the current status of instance {instance_name} in compartment {compartment_id}? Include health status, metrics, and any alerts.",
        "variables": {
            "instance_name": {"type": "string", "description": "Name of the compute instance"},
            "compartment_id": {"type": "string", "description": "OCI compartment ID"}
        },
        "requires_role": None
    },
    {
        "name": "List VCN Configuration",
        "description": "Get detailed VCN configuration and network topology",
        "category": "Infrastructure",
        "template_text": "Show me the network configuration for VCN {vcn_name} in compartment {compartment_id}, including subnets, route tables, and security lists.",
        "variables": {
            "vcn_name": {"type": "string", "description": "Name of the Virtual Cloud Network"},
            "compartment_id": {"type": "string", "description": "OCI compartment ID"}
        },
        "requires_role": None
    },
    {
        "name": "Storage Usage Analysis",
        "description": "Analyze storage volume usage and performance",
        "category": "Infrastructure",
        "template_text": "Analyze storage volumes in compartment {compartment_id}. Show usage, performance metrics, and recommendations for optimization.",
        "variables": {
            "compartment_id": {"type": "string", "description": "OCI compartment ID"}
        },
        "requires_role": None
    },
    {
        "name": "Database Health Check",
        "description": "Check database health and performance metrics",
        "category": "Infrastructure",
        "template_text": "Check the health and performance of database {database_name} in compartment {compartment_id}. Include connection status, resource usage, and any alerts.",
        "variables": {
            "database_name": {"type": "string", "description": "Name of the database"},
            "compartment_id": {"type": "string", "description": "OCI compartment ID"}
        },
        "requires_role": None
    },
    
    # Monitoring Templates
    {
        "name": "Active Alerts Summary",
        "description": "Get summary of all active alerts and their severity",
        "category": "Monitoring",
        "template_text": "Show me all active alerts in compartment {compartment_id}. Group by severity and include recommended actions.",
        "variables": {
            "compartment_id": {"type": "string", "description": "OCI compartment ID"}
        },
        "requires_role": None
    },
    {
        "name": "CPU Utilization Analysis",
        "description": "Analyze CPU utilization patterns and trends",
        "category": "Monitoring",
        "template_text": "Analyze CPU utilization for {resource_name} over the last {time_period}. Identify patterns, peaks, and provide optimization recommendations.",
        "variables": {
            "resource_name": {"type": "string", "description": "Name of the resource to analyze"},
            "time_period": {"type": "string", "description": "Time period for analysis (e.g., '24 hours', '7 days')"}
        },
        "requires_role": None
    },
    {
        "name": "Memory Usage Investigation",
        "description": "Investigate memory usage and potential leaks",
        "category": "Monitoring",
        "template_text": "Investigate memory usage for {resource_name}. Check for memory leaks, high usage patterns, and provide recommendations.",
        "variables": {
            "resource_name": {"type": "string", "description": "Name of the resource to investigate"}
        },
        "requires_role": None
    },
    {
        "name": "Custom Metric Analysis",
        "description": "Analyze custom metrics and create insights",
        "category": "Monitoring",
        "template_text": "Analyze the {metric_name} metric for {resource_name} over {time_period}. Identify trends and anomalies.",
        "variables": {
            "metric_name": {"type": "string", "description": "Name of the metric to analyze"},
            "resource_name": {"type": "string", "description": "Resource name"},
            "time_period": {"type": "string", "description": "Analysis time period"}
        },
        "requires_role": None
    },
    
    # Troubleshooting Templates
    {
        "name": "Connection Timeout Diagnosis",
        "description": "Diagnose and resolve connection timeout issues",
        "category": "Troubleshooting",
        "template_text": "I'm experiencing connection timeouts with {service_name}. Help me diagnose the issue and provide step-by-step resolution.",
        "variables": {
            "service_name": {"type": "string", "description": "Name of the service experiencing issues"}
        },
        "requires_role": None
    },
    {
        "name": "High Latency Investigation",
        "description": "Investigate and resolve high latency issues",
        "category": "Troubleshooting",
        "template_text": "My application {app_name} is experiencing high latency. Analyze the performance and suggest optimization steps.",
        "variables": {
            "app_name": {"type": "string", "description": "Name of the application"}
        },
        "requires_role": None
    },
    {
        "name": "Service Unavailable Troubleshooting",
        "description": "Troubleshoot service unavailability issues",
        "category": "Troubleshooting",
        "template_text": "Service {service_name} is not responding. Help me troubleshoot the issue and restore service availability.",
        "variables": {
            "service_name": {"type": "string", "description": "Name of the unavailable service"}
        },
        "requires_role": None
    },
    {
        "name": "Performance Degradation Analysis",
        "description": "Analyze and resolve performance degradation",
        "category": "Troubleshooting",
        "template_text": "Performance of {resource_name} has degraded since {start_time}. Analyze the cause and provide resolution steps.",
        "variables": {
            "resource_name": {"type": "string", "description": "Name of the resource"},
            "start_time": {"type": "string", "description": "When the degradation started"}
        },
        "requires_role": None
    },
    
    # Cost Optimization Templates
    {
        "name": "Compartment Cost Analysis",
        "description": "Analyze costs for a specific compartment",
        "category": "Cost",
        "template_text": "Analyze the costs for compartment {compartment_id} over the last {period}. Identify top spending resources and optimization opportunities.",
        "variables": {
            "compartment_id": {"type": "string", "description": "OCI compartment ID"},
            "period": {"type": "string", "description": "Analysis period (e.g., '30 days', '3 months')"}
        },
        "requires_role": None
    },
    {
        "name": "Resource Rightsizing",
        "description": "Analyze resource usage for rightsizing opportunities",
        "category": "Cost",
        "template_text": "Analyze resource utilization for {resource_type} in compartment {compartment_id} and suggest rightsizing opportunities.",
        "variables": {
            "resource_type": {"type": "string", "description": "Type of resource (compute, storage, network)"},
            "compartment_id": {"type": "string", "description": "OCI compartment ID"}
        },
        "requires_role": None
    },
    {
        "name": "Unused Resources Identification",
        "description": "Identify unused or underutilized resources",
        "category": "Cost",
        "template_text": "Identify unused or underutilized resources in compartment {compartment_id} that can be terminated or downsized.",
        "variables": {
            "compartment_id": {"type": "string", "description": "OCI compartment ID"}
        },
        "requires_role": None
    },
    {
        "name": "Cost Trend Analysis",
        "description": "Analyze cost trends and predict future spending",
        "category": "Cost",
        "template_text": "Analyze cost trends for compartment {compartment_id} over the last {period} and predict future spending patterns.",
        "variables": {
            "compartment_id": {"type": "string", "description": "OCI compartment ID"},
            "period": {"type": "string", "description": "Analysis period"}
        },
        "requires_role": None
    },
    
    # Remediation Templates
    {
        "name": "Automated Instance Restart",
        "description": "Safely restart unresponsive instances",
        "category": "Remediation",
        "template_text": "Instance {instance_name} is unresponsive. Create an automated remediation plan to safely restart it.",
        "variables": {
            "instance_name": {"type": "string", "description": "Name of the instance to restart"}
        },
        "requires_role": "operator"
    },
    {
        "name": "Scale Out Application",
        "description": "Scale out application to handle increased load",
        "category": "Remediation",
        "template_text": "Application {app_name} is experiencing high load. Create a scaling plan to add {scale_count} additional instances.",
        "variables": {
            "app_name": {"type": "string", "description": "Name of the application"},
            "scale_count": {"type": "number", "description": "Number of instances to add"}
        },
        "requires_role": "operator"
    },
    {
        "name": "Storage Volume Expansion",
        "description": "Expand storage volumes approaching capacity",
        "category": "Remediation",
        "template_text": "Storage volume {volume_name} is {usage_percent}% full. Create a plan to expand it by {expansion_size}.",
        "variables": {
            "volume_name": {"type": "string", "description": "Name of the storage volume"},
            "usage_percent": {"type": "number", "description": "Current usage percentage"},
            "expansion_size": {"type": "string", "description": "Size to expand (e.g., '100GB', '1TB')"}
        },
        "requires_role": "operator"
    },
    
    # Analysis Templates
    {
        "name": "Security Assessment",
        "description": "Perform security assessment of resources",
        "category": "Analysis",
        "template_text": "Perform a security assessment of compartment {compartment_id}. Check for vulnerabilities, misconfigurations, and compliance issues.",
        "variables": {
            "compartment_id": {"type": "string", "description": "OCI compartment ID"}
        },
        "requires_role": None
    },
    {
        "name": "Capacity Planning",
        "description": "Analyze current usage and plan for future capacity",
        "category": "Analysis",
        "template_text": "Analyze current resource usage in compartment {compartment_id} and provide capacity planning recommendations for the next {planning_period}.",
        "variables": {
            "compartment_id": {"type": "string", "description": "OCI compartment ID"},
            "planning_period": {"type": "string", "description": "Planning period (e.g., '6 months', '1 year')"}
        },
        "requires_role": None
    },
    {
        "name": "Compliance Report",
        "description": "Generate compliance report for resources",
        "category": "Analysis",
        "template_text": "Generate a compliance report for compartment {compartment_id} against {compliance_standard} standards.",
        "variables": {
            "compartment_id": {"type": "string", "description": "OCI compartment ID"},
            "compliance_standard": {"type": "string", "description": "Compliance standard (e.g., 'SOC2', 'HIPAA', 'PCI DSS')"}
        },
        "requires_role": "operator"
    }
]

def init_default_templates():
    """Initialize default query templates in the database"""
    logger.info("Starting initialization of default query templates...")
    
    # Create tables if they don't exist
    create_tables()
    
    db = next(get_db())
    try:
        # Check if templates already exist
        existing_count = db.query(QueryTemplate).count()
        if existing_count > 0:
            logger.info(f"Found {existing_count} existing templates. Skipping initialization.")
            return
        
        # Create default templates
        created_count = 0
        for template_data in DEFAULT_TEMPLATES:
            try:
                template = QueryTemplate(
                    name=template_data["name"],
                    description=template_data["description"],
                    category=template_data["category"],
                    template_text=template_data["template_text"],
                    variables=template_data["variables"],
                    requires_role=template_data.get("requires_role"),
                    is_active=True
                )
                
                db.add(template)
                created_count += 1
                logger.info(f"Created template: {template.name}")
                
            except Exception as e:
                logger.error(f"Failed to create template {template_data['name']}: {e}")
                continue
        
        db.commit()
        logger.info(f"Successfully created {created_count} default query templates")
        
        # Print summary by category
        categories = {}
        for template in DEFAULT_TEMPLATES:
            category = template["category"]
            categories[category] = categories.get(category, 0) + 1
        
        logger.info("Templates created by category:")
        for category, count in categories.items():
            logger.info(f"  {category}: {count} templates")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to initialize default templates: {e}")
        raise
    finally:
        db.close()

def main():
    """Main function"""
    try:
        init_default_templates()
        logger.info("Default query templates initialization completed successfully!")
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 