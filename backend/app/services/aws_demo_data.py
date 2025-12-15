AWS_OVERVIEW = {
    "account": {
        "id": "123456789012",
        "alias": "genai-cloudops-demo",
        "region": "us-east-1",
        "environments": [
            {"name": "Production", "status": "healthy"},
            {"name": "Staging", "status": "warning"},
            {"name": "Development", "status": "healthy"}
        ]
    },
    "summary": {
        "total_services": 18,
        "resources_discovered": 124,
        "active_alerts": 5,
        "open_incidents": 1,
        "cost_month_to_date": 18243.56,
        "budget_burn_rate": 0.72,
        "optimization_opportunities": 6
    },
    "highlights": [
        {
            "id": "hl-001",
            "title": "ECS service scaling conservatively",
            "impact": "performance",
            "severity": "medium",
            "summary": "Average CPU utilization at 78% with spike risk during business hours.",
            "recommendation": "Increase desired count or enable autoscaling target tracking."
        },
        {
            "id": "hl-002",
            "title": "RDS instance oversized",
            "impact": "cost",
            "severity": "low",
            "summary": "db-prod-aurora instance running at 14% average CPU and 1% IO utilization.",
            "recommendation": "Downsize to r6g.large or enable autoscaling reader endpoints."
        },
        {
            "id": "hl-003",
            "title": "IAM access keys nearing rotation threshold",
            "impact": "security",
            "severity": "high",
            "summary": "3 programmatic users exceed 80 days since last key rotation.",
            "recommendation": "Rotate keys and enforce shorter credential lifetime policy."
        }
    ]
}

AWS_MONITORING = {
    "summary": {
        "compartment_id": "aws:account:123456789012",
        "total_alarms": 7,
        "active_alarms": 3,
        "severity_breakdown": {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 1,
            "INFO": 0
        },
        "recent_activity": {
            "summary": "3 CloudWatch alarms + 2 EKS cluster insights",
            "oci_alarms": 3,
            "resource_alerts": 2,
            "last_updated": "2025-11-08T18:59:56.155640",
            "alert_rate": 0.8,
            "resolved_alerts": 1,
            "new_alerts": 2
        },
        "top_alerts": [
            {
                "id": "aws_alarm_eks_nodes",
                "display_name": "EKS node capacity",
                "severity": "CRITICAL",
                "lifecycle_state": "ACTIVE",
                "is_enabled": True,
                "metric_compartment_id": "aws:eks:cluster/analytics-prod",
                "namespace": "AWS/EKS",
                "query": "NodeDiskUtilization > 85",
                "rule_name": "EksDiskPressure",
                "time_created": "2025-11-08T18:50:12.155640",
                "time_updated": "2025-11-08T18:59:56.155640",
                "source": "aws_cloudwatch"
            },
            {
                "id": "aws_alarm_ec2_cpu",
                "display_name": "EC2 CPU spike",
                "severity": "HIGH",
                "lifecycle_state": "ACTIVE",
                "is_enabled": True,
                "metric_compartment_id": "aws:ec2:i-0a12bc34def567890",
                "namespace": "AWS/EC2",
                "query": "CPUUtilization > 75",
                "rule_name": "AsgScaleUp",
                "time_created": "2025-11-08T17:29:12.155640",
                "time_updated": "2025-11-08T18:24:56.155640",
                "source": "aws_cloudwatch"
            }
        ],
        "timestamp": "2025-11-08T18:59:56.155640",
        "health_score": 78
    },
    "active_alarms": [
        {
            "id": "aws_alarm_ec2_cpu",
            "display_name": "EC2 CPU spike",
            "severity": "HIGH",
            "lifecycle_state": "ACTIVE",
            "is_enabled": True,
            "metric_compartment_id": "aws:ec2:i-0a12bc34def567890",
            "namespace": "AWS/EC2",
            "query": "CPUUtilization > 75",
            "rule_name": "AsgScaleUp",
            "time_created": "2025-11-08T17:29:12.155640",
            "time_updated": "2025-11-08T18:24:56.155640",
            "source": "aws_cloudwatch"
        },
        {
            "id": "aws_alarm_eks_nodes",
            "display_name": "EKS node capacity",
            "severity": "CRITICAL",
            "lifecycle_state": "ACTIVE",
            "is_enabled": True,
            "metric_compartment_id": "aws:eks:cluster/analytics-prod",
            "namespace": "AWS/EKS",
            "query": "NodeDiskUtilization > 85",
            "rule_name": "EksDiskPressure",
            "time_created": "2025-11-08T18:50:12.155640",
            "time_updated": "2025-11-08T18:59:56.155640",
            "source": "aws_cloudwatch"
        },
        {
            "id": "aws_alarm_rds_latency",
            "display_name": "RDS write latency",
            "severity": "MEDIUM",
            "lifecycle_state": "ACTIVE",
            "is_enabled": True,
            "metric_compartment_id": "aws:rds:prod-aurora-cluster",
            "namespace": "AWS/RDS",
            "query": "WriteLatency > 35",
            "rule_name": "RdsLatency",
            "time_created": "2025-11-08T12:14:45.155640",
            "time_updated": "2025-11-08T17:12:05.155640",
            "source": "aws_cloudwatch"
        }
    ],
    "recent_history": [
        {
            "alarm_id": "aws_alarm_ec2_cpu",
            "alarm_name": "EC2 CPU spike",
            "status": "FIRING",
            "timestamp": "2025-11-08T18:24:56.155640",
            "summary": "Alarm EC2 CPU spike - HIGH severity triggered",
            "suppressed": False,
            "severity": "HIGH",
            "namespace": "AWS/EC2"
        },
        {
            "alarm_id": "aws_alarm_eks_nodes",
            "alarm_name": "EKS node capacity",
            "status": "FIRING",
            "timestamp": "2025-11-08T18:19:32.155640",
            "summary": "Alarm EKS node capacity - CRITICAL severity triggered",
            "suppressed": False,
            "severity": "CRITICAL",
            "namespace": "AWS/EKS"
        },
        {
            "alarm_id": "aws_alarm_lambda_errors",
            "alarm_name": "Lambda error spike",
            "status": "OK",
            "timestamp": "2025-11-08T17:03:21.155640",
            "summary": "Alarm Lambda error spike resolved",
            "suppressed": False,
            "severity": "MEDIUM",
            "namespace": "AWS/Lambda"
        }
    ],
    "quick_stats": {
        "uptime_score": 97.2,
        "performance_score": 82.5,
        "security_alerts": 4
    },
    "trends": {
        "total_alarms_trend": 1,
        "critical_alerts_trend": 1,
        "health_score_trend": -2.3
    },
    "eks": {
        "cluster_count": 3,
        "active_nodes": 68,
        "pods_running": 412,
        "failing_workloads": 5,
        "clusters": [
            {
                "name": "analytics-prod",
                "region": "us-east-1",
                "status": "DEGRADED",
                "health_score": 62,
                "node_groups": 6,
                "node_pressure": "Disk pressure",
                "pod_restarts_24h": 18
            },
            {
                "name": "payments-core",
                "region": "us-west-2",
                "status": "HEALTHY",
                "health_score": 91,
                "node_groups": 4,
                "node_pressure": None,
                "pod_restarts_24h": 2
            },
            {
                "name": "genai-sandbox",
                "region": "eu-central-1",
                "status": "WARNING",
                "health_score": 74,
                "node_groups": 3,
                "node_pressure": "CPU throttling",
                "pod_restarts_24h": 9
            }
        ],
        "insights": [
            {
                "id": "eks-capacity",
                "severity": "HIGH",
                "summary": "analytics-prod cluster nearing node storage capacity",
                "recommendation": "Add gp3 nodes or enable cluster autoscaler storage expansion"
            },
            {
                "id": "eks-pod-restarts",
                "severity": "MEDIUM",
                "summary": "Spike in pod restarts within genai-sandbox cluster",
                "recommendation": "Review deployment health-checks and investigate failing pods"
            }
        ]
    },
    "metrics": [
        {
            "service": "EC2",
            "metric": "CPUUtilization",
            "namespace": "AWS/EC2",
            "dimensions": {"InstanceId": "i-0a12bc34def567890"},
            "statistics": {
                "period_minutes": 5,
                "average": 38.2,
                "maximum": 64.5,
                "minimum": 12.4,
                "unit": "Percent"
            },
            "trend": [43, 35, 28, 32, 40, 46, 51, 47, 39, 36, 34, 38]
        },
        {
            "service": "RDS",
            "metric": "FreeableMemory",
            "namespace": "AWS/RDS",
            "dimensions": {"DBInstanceIdentifier": "prod-aurora-cluster"},
            "statistics": {
                "period_minutes": 5,
                "average": 12.8,
                "maximum": 14.5,
                "minimum": 11.6,
                "unit": "GB"
            },
            "trend": [13.2, 12.9, 12.5, 12.1, 11.9, 12.0, 12.4, 12.8, 13.1, 13.0, 12.7, 12.6]
        },
        {
            "service": "Lambda",
            "metric": "Errors",
            "namespace": "AWS/Lambda",
            "dimensions": {"FunctionName": "genai-api-router"},
            "statistics": {
                "period_minutes": 1,
                "average": 2.1,
                "maximum": 7,
                "minimum": 0,
                "unit": "Count"
            },
            "trend": [0, 1, 0, 3, 2, 1, 5, 7, 6, 3, 2, 1]
        }
    ],
    "alerts": [
        {
            "id": "alarm-ec2-cpu",
            "title": "EC2 CPU spike",
            "severity": "medium",
            "service": "EC2",
            "resource": "i-0a12bc34def567890",
            "state": "ALARM",
            "last_triggered": "2025-11-07T22:35:00Z",
            "description": "CPU utilization exceeded 80% for 15 minutes",
            "recommended_action": "Increase ASG desired capacity from 4 to 6 instances"
        },
        {
            "id": "alarm-rds-latency",
            "title": "RDS write latency",
            "severity": "low",
            "service": "RDS",
            "resource": "prod-aurora-cluster",
            "state": "OK",
            "last_triggered": "2025-11-06T14:12:00Z",
            "description": "Commit latency exceeded 40ms threshold",
            "recommended_action": "Evaluate provisioned IOPS or add read replica"
        },
        {
            "id": "alarm-eks-restart",
            "title": "EKS pod restart storm",
            "severity": "high",
            "service": "EKS",
            "resource": "cluster/genai-sandbox",
            "state": "ALARM",
            "last_triggered": "2025-11-08T16:02:00Z",
            "description": "Pod restart rate exceeded 10 per 15 minutes",
            "recommended_action": "Inspect Deployment rollout history and failing pods"
        }
    ],
    "logs": {
        "recent_findings": [
            {
                "time": "2025-11-08T18:15:18Z",
                "source": "CloudWatchLogs",
                "service": "EKS",
                "summary": "DaemonSet restart detected",
                "details": "Cluster analytics-prod has daemonset aws-node restarting across node group ng-app-1"
            },
            {
                "time": "2025-11-07T21:42:18Z",
                "source": "CloudWatchLogs",
                "service": "ECS",
                "summary": "Task restart detected due to image pull retry",
                "details": "Cluster analytics-prod had 3 task restarts in last hour"
            },
            {
                "time": "2025-11-07T19:03:51Z",
                "source": "GuardDuty",
                "service": "IAM",
                "summary": "Anomalous API activity from VPN IP",
                "details": "User ci-bot attempted DescribeInstances in restricted account"
            }
        ]
    },
    "last_updated": "2025-11-08T18:59:56.155640"
}

AWS_MONITORING_SCOPES = [
    {
        "id": "aws:region:us-east-1",
        "name": "US East (N. Virginia)",
        "code": "us-east-1",
        "type": "region",
        "lifecycle_state": "ACTIVE",
        "description": "Primary production workloads"
    },
    {
        "id": "aws:region:us-west-2",
        "name": "US West (Oregon)",
        "code": "us-west-2",
        "type": "region",
        "lifecycle_state": "ACTIVE",
        "description": "Disaster recovery and analytics"
    },
    {
        "id": "aws:region:eu-central-1",
        "name": "EU (Frankfurt)",
        "code": "eu-central-1",
        "type": "region",
        "lifecycle_state": "ACTIVE",
        "description": "EMEA workloads and sandbox"
    }
]

AWS_COST = {
    "summary": {
        "month_to_date_spend": 18243.56,
        "forecast_end_of_month": 24510.32,
        "budget": 25000.0,
        "variance": -489.68,
        "optimization_estimate": 3295.40
    },
    "service_breakdown": [
        {"service": "EC2", "spend": 7210.45, "change_percent": 8.4},
        {"service": "RDS", "spend": 3521.11, "change_percent": 3.1},
        {"service": "S3", "spend": 1889.24, "change_percent": 1.2},
        {"service": "Lambda", "spend": 943.55, "change_percent": -4.6},
        {"service": "CloudFront", "spend": 822.67, "change_percent": 6.8},
        {"service": "EKS", "spend": 1934.54, "change_percent": 11.3}
    ],
    "recommendations": [
        {
            "id": "cost-ec2-ri",
            "title": "Convertible RI coverage opportunity",
            "service": "EC2",
            "potential_savings": 1025.12,
            "term": "1 year",
            "details": "m6i.2xlarge fleet at 67% On-Demand – recommend purchasing 5 convertible RIs for production ASG."
        },
        {
            "id": "cost-s3-lifecycle",
            "title": "Enable S3 intelligent tiering",
            "service": "S3",
            "potential_savings": 418.33,
            "term": "monthly",
            "details": "Bucket analytics-raw-data has 27 TB of infrequently accessed data older than 45 days."
        }
    ]
}

AWS_SECURITY = {
    "summary": {
        "critical_findings": 1,
        "high_findings": 4,
        "medium_findings": 9,
        "low_findings": 12,
        "iam_users_with_keys": 18,
        "unused_security_groups": 7
    },
    "findings": [
        {
            "id": "sec-iam-keys",
            "title": "Unused IAM access keys",
            "severity": "high",
            "service": "IAM",
            "resource": "user/devops-ci",
            "details": "Access keys have not been used for 120 days.",
            "recommendation": "Disable or delete unused keys and enforce rotation policy."
        },
        {
            "id": "sec-s3-public",
            "title": "S3 bucket allows public read",
            "severity": "critical",
            "service": "S3",
            "resource": "bucket/analytics-exports",
            "details": "Bucket policy grants public read access.",
            "recommendation": "Restrict bucket policy and enable Block Public Access."
        }
    ],
    "rbac": {
        "roles": [
            {
                "name": "AdminAccess",
                "principals": 6,
                "last_audited": "2025-10-15",
                "risk": "medium"
            },
            {
                "name": "PowerUserAccess",
                "principals": 11,
                "last_audited": "2025-09-02",
                "risk": "medium"
            },
            {
                "name": "ReadOnlyAccess",
                "principals": 34,
                "last_audited": "2025-11-01",
                "risk": "low"
            }
        ],
        "policies_to_review": [
            {
                "name": "InlinePolicy-ECSDeploy",
                "principal": "role/ecs-deployer",
                "finding": "Allows iam:PassRole to *",
                "recommendation": "Scope pass role permissions to deployment roles only."
            }
        ]
    }
}

AWS_AUTOMATION = {
    "playbooks": [
        {
            "id": "pb-scale-asg",
            "name": "Scale Auto Scaling Group",
            "category": "performance",
            "description": "Adjust desired capacity for genai-app ASG when sustained CPU exceeds 75%.",
            "risk": "low",
            "last_validated": "2025-11-05",
            "steps": [
                "Retrieve current ASG metrics",
                "If desired capacity < max, increase by 2",
                "Notify #cloud-ops channel with change context"
            ]
        },
        {
            "id": "pb-restart-ec2",
            "name": "Restart EC2 instance",
            "category": "operations",
            "description": "Gracefully stop/start EC2 instance when health checks fail and alternative capacity exists.",
            "risk": "medium",
            "last_validated": "2025-10-29",
            "steps": [
                "Drain instance from load balancer",
                "Wait for session drain",
                "Stop instance and wait until stopped",
                "Start instance and verify health"
            ]
        }
    ],
    "approvals": {
        "required": True,
        "approvers": ["aws-platform-lead", "oncall-sre"],
        "pending": 1
    }
}

AWS_RESOURCES = {
    "compute": {
        "ec2": {
            "running_instances": 42,
            "average_cpu": 41.7,
            "auto_scaling_groups": 7,
            "eks_clusters": 3
        },
        "lambda": {
            "active_functions": 58,
            "avg_duration_ms": 112,
            "error_rate": 0.004
        }
    },
    "storage": {
        "s3": {
            "total_buckets": 26,
            "object_count": 92873421,
            "storage_tb": 183.4
        },
        "efs": {
            "file_systems": 4,
            "avg_utilization": 52.3
        }
    },
    "databases": {
        "rds": {
            "instances": 12,
            "aurora_clusters": 3,
            "avg_cpu": 24.5
        },
        "dynamodb": {
            "tables": 18,
            "throttle_events": 3
        }
    },
    "networking": {
        "vpcs": 5,
        "subnets": 48,
        "load_balancers": {
            "alb": 9,
            "nlb": 3,
            "gateway": 2
        },
        "vpn_connections": 4
    }
}
