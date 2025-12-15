# 📡 API Reference

Complete documentation for the GenAI CloudOps Dashboard REST API.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Core Endpoints](#core-endpoints)
- [Module APIs](#module-apis)
- [WebSocket API](#websocket-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [SDK Examples](#sdk-examples)

## Overview

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

### API Version
- **Current Version**: `v1`
- **Base Path**: `/api/v1`

### Content Types
- **Request**: `application/json`
- **Response**: `application/json`
- **Metrics**: `text/plain` (Prometheus format)

### Response Format
```json
{
  "status": "success|error",
  "data": {},
  "message": "Optional message",
  "timestamp": "2025-01-31T12:00:00Z",
  "request_id": "uuid-v4"
}
```

## Authentication

### JWT Authentication

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "role": "admin"
    }
  }
}
```

#### Token Usage
```http
GET /api/v1/protected-endpoint
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer current-token
```

#### Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer current-token
```

### Permissions

#### Role-Based Access Control
- **admin**: Full access to all resources
- **operator**: Read/write access, limited admin functions
- **viewer**: Read-only access

#### Permission Format
```
resource:action
```

Examples:
- `monitoring:read` - View monitoring data
- `remediation:execute` - Execute remediation actions
- `genai:admin` - Manage AI configurations

## Core Endpoints

### Health Checks

#### Application Health
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-31T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "oci": "healthy",
    "genai": "healthy"
  }
}
```

#### Detailed Health
```http
GET /api/v1/health/detailed
Authorization: Bearer token
```

#### Component Health
```http
GET /api/v1/health/{component}
Authorization: Bearer token
```

Components: `database`, `redis`, `oci`, `genai`, `kubernetes`

### User Management

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer token
```

#### Update Profile
```http
PUT /api/v1/auth/profile
Authorization: Bearer token
Content-Type: application/json

{
  "email": "new-email@example.com",
  "preferences": {
    "theme": "dark",
    "notifications": {
      "email": true,
      "slack": false
    }
  }
}
```

## Module APIs

### 1. Monitoring Service

#### Get Resources Overview
```http
GET /api/v1/monitoring/resources
Authorization: Bearer token
```

**Query Parameters:**
- `compartment_id` (optional): Filter by OCI compartment
- `resource_type` (optional): Filter by resource type
- `include_metrics` (optional): Include real-time metrics

**Response:**
```json
{
  "status": "success",
  "data": {
    "summary": {
      "total_resources": 45,
      "healthy": 40,
      "warning": 3,
      "critical": 2
    },
    "resources": [
      {
        "id": "ocid1.instance.oc1..xxx",
        "name": "web-server-01",
        "type": "compute_instance",
        "state": "RUNNING",
        "health_score": 85,
        "metrics": {
          "cpu_utilization": 65.2,
          "memory_utilization": 78.5,
          "network_in": 1024000,
          "network_out": 2048000
        },
        "compartment": "Production",
        "availability_domain": "AD-1",
        "last_updated": "2025-01-31T12:00:00Z"
      }
    ]
  }
}
```

#### Get Resource Details
```http
GET /api/v1/monitoring/resources/{resource_id}
Authorization: Bearer token
```

#### Get Resource Metrics
```http
GET /api/v1/monitoring/resources/{resource_id}/metrics
Authorization: Bearer token
```

**Query Parameters:**
- `start_time`: ISO 8601 timestamp
- `end_time`: ISO 8601 timestamp
- `resolution`: `1m`, `5m`, `15m`, `1h`, `1d`

#### Get Alerts
```http
GET /api/v1/monitoring/alerts
Authorization: Bearer token
```

**Query Parameters:**
- `status`: `active`, `resolved`, `acknowledged`
- `severity`: `critical`, `high`, `medium`, `low`
- `limit`: Number of results (default: 50)

### 2. GenAI Service

#### Chat with AI
```http
POST /api/v1/genai/chat
Authorization: Bearer token
Content-Type: application/json

{
  "message": "What's the status of my infrastructure?",
  "context": {
    "compartment_id": "ocid1.compartment.oc1..xxx",
    "include_metrics": true
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "response": "Your infrastructure is generally healthy with 40 out of 45 resources in good state...",
    "conversation_id": "uuid",
    "context_used": true,
    "model_used": "llama3-8b-8192",
    "tokens_used": 150,
    "response_time": 2.5
  }
}
```

#### Generate Analysis
```http
POST /api/v1/genai/analyze
Authorization: Bearer token
Content-Type: application/json

{
  "prompt_type": "analysis",
  "data": {
    "resource_metrics": {...},
    "alert_data": {...},
    "time_range": "1h"
  }
}
```

#### Get Conversation History
```http
GET /api/v1/genai/conversations
Authorization: Bearer token
```

#### Prompt Management
```http
GET /api/v1/genai/prompts/types
Authorization: Bearer token
```

```http
POST /api/v1/genai/prompts/validate
Authorization: Bearer token
Content-Type: application/json

{
  "prompt_type": "remediation",
  "parameters": {
    "issue_details": "High CPU usage",
    "resource_info": "..."
  }
}
```

### 3. Kubernetes Service

#### Get Cluster Status
```http
GET /api/v1/kubernetes/clusters
Authorization: Bearer token
```

#### Get Pod Health
```http
GET /api/v1/kubernetes/pods/health
Authorization: Bearer token
```

**Query Parameters:**
- `cluster_id` (optional): Filter by cluster
- `namespace` (optional): Filter by namespace
- `status` (optional): Filter by pod status

**Response:**
```json
{
  "status": "success",
  "data": {
    "summary": {
      "total_pods": 150,
      "running": 145,
      "pending": 2,
      "failed": 3,
      "health_score": 96.7
    },
    "pods": [
      {
        "name": "frontend-deployment-xyz",
        "namespace": "production",
        "status": "Running",
        "ready": "3/3",
        "restarts": 0,
        "age": "5d",
        "node": "worker-node-1",
        "cpu_usage": "150m",
        "memory_usage": "256Mi",
        "health_score": 100
      }
    ]
  }
}
```

#### RBAC Analysis
```http
GET /api/v1/kubernetes/rbac/analysis
Authorization: Bearer token
```

#### Get Pod Logs
```http
GET /api/v1/kubernetes/pods/{pod_name}/logs
Authorization: Bearer token
```

**Query Parameters:**
- `namespace`: Pod namespace
- `container` (optional): Container name
- `lines` (optional): Number of lines (default: 100)
- `since` (optional): Time duration (e.g., "1h", "30m")

### 4. Cost Analyzer

#### Get Cost Summary
```http
GET /api/v1/cost/summary
Authorization: Bearer token
```

**Query Parameters:**
- `compartment_id` (optional): Filter by compartment
- `time_range`: `7d`, `30d`, `90d`, `1y`
- `group_by`: `service`, `compartment`, `resource`

**Response:**
```json
{
  "status": "success",
  "data": {
    "current_month": {
      "total_cost": 1250.75,
      "currency": "USD",
      "trend": {
        "percentage_change": 15.2,
        "direction": "increase"
      }
    },
    "breakdown": [
      {
        "service": "Compute",
        "cost": 650.25,
        "percentage": 52.1,
        "instances": 15
      },
      {
        "service": "Database",
        "cost": 400.00,
        "percentage": 32.0,
        "instances": 3
      }
    ],
    "forecast": {
      "next_month": 1350.00,
      "confidence": 85
    }
  }
}
```

#### Get Optimization Recommendations
```http
GET /api/v1/cost/optimization
Authorization: Bearer token
```

#### Get Cost Alerts
```http
GET /api/v1/cost/alerts
Authorization: Bearer token
```

### 5. Access Analyzer

#### Get RBAC Overview
```http
GET /api/v1/access/rbac/overview
Authorization: Bearer token
```

#### Get Security Recommendations
```http
GET /api/v1/access/recommendations
Authorization: Bearer token
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "security_score": 78,
    "recommendations": [
      {
        "id": "rbac-001",
        "title": "Remove excessive permissions",
        "description": "Service account 'app-service' has cluster-admin privileges but only needs read access",
        "severity": "high",
        "risk_score": 85,
        "remediation": {
          "type": "rbac_update",
          "action": "Replace ClusterRoleBinding with Role",
          "commands": ["kubectl delete clusterrolebinding app-service-binding"]
        }
      }
    ]
  }
}
```

#### Analyze IAM Policies
```http
GET /api/v1/access/iam/analysis
Authorization: Bearer token
```

### 6. Remediation Service

#### Get Remediation Plans
```http
GET /api/v1/remediation/plans
Authorization: Bearer token
```

#### Submit Remediation Request
```http
POST /api/v1/remediation/submit
Authorization: Bearer token
Content-Type: application/json

{
  "plan_id": "k8s_pod_restart",
  "context": {
    "pod_name": "frontend-deployment-xyz",
    "namespace": "production"
  },
  "force_approval": false
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "execution_id": "rem_1706782800_abc123",
    "execution_status": "requires_approval",
    "risk_assessment": {
      "overall_risk": "low",
      "risk_factors": ["Pod restart required"],
      "recommendation": "Safe for automatic execution with monitoring"
    },
    "estimated_duration": 3
  }
}
```

#### Approve Remediation
```http
POST /api/v1/remediation/approve/{execution_id}
Authorization: Bearer token
Content-Type: application/json

{
  "comments": "Approved after reviewing impact"
}
```

#### Get Execution Status
```http
GET /api/v1/remediation/executions/{execution_id}
Authorization: Bearer token
```

### 7. Notification Service

#### Send Notification
```http
POST /api/v1/notifications/send
Authorization: Bearer token
Content-Type: application/json

{
  "notification_type": "alert",
  "severity": "high",
  "title": "High CPU Usage Alert",
  "message": "CPU usage exceeded 90% on web-server-01",
  "data": {
    "resource_id": "ocid1.instance.oc1..xxx",
    "metric_value": 95.2,
    "threshold": 90
  },
  "recipients": ["System Administrators"],
  "channels": ["email", "slack"]
}
```

#### Get Notification History
```http
GET /api/v1/notifications/history
Authorization: Bearer token
```

### 8. Optional Enhancements

#### Prometheus Metrics
```http
GET /api/v1/enhancements/metrics
```

**Response Format:** Prometheus text format
```
# HELP genai_cloudops_http_requests_total Total HTTP requests
# TYPE genai_cloudops_http_requests_total counter
genai_cloudops_http_requests_total{method="GET",endpoint="/api/v1/health",status_code="200"} 1542
```

#### Grafana Status
```http
GET /api/v1/enhancements/grafana/status
Authorization: Bearer token
```

#### Create Custom Metric
```http
POST /api/v1/enhancements/metrics/custom
Authorization: Bearer token
Content-Type: application/json

{
  "name": "business_kpi",
  "metric_type": "gauge",
  "description": "Business KPI metric",
  "labels": ["department", "region"],
  "unit": "count"
}
```

## WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/realtime');
```

### Authentication
```javascript
// Send authentication message after connection
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your-jwt-token'
}));
```

### Message Types

#### Subscribe to Updates
```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['alerts', 'metrics', 'remediation'],
  filters: {
    compartment_id: 'ocid1.compartment.oc1..xxx'
  }
}));
```

#### Real-time Metrics
```javascript
// Incoming metric updates
{
  type: 'metric_update',
  timestamp: '2025-01-31T12:00:00Z',
  data: {
    resource_id: 'ocid1.instance.oc1..xxx',
    metric_name: 'cpu_utilization',
    value: 78.5,
    unit: 'percent'
  }
}
```

#### Alert Notifications
```javascript
// Incoming alert
{
  type: 'alert',
  timestamp: '2025-01-31T12:00:00Z',
  data: {
    id: 'alert_123',
    title: 'High CPU Usage',
    severity: 'high',
    resource: 'web-server-01',
    message: 'CPU usage exceeded threshold'
  }
}
```

#### Remediation Updates
```javascript
// Remediation status update
{
  type: 'remediation_update',
  timestamp: '2025-01-31T12:00:00Z',
  data: {
    execution_id: 'rem_1706782800_abc123',
    status: 'completed',
    progress: 100,
    message: 'Pod restart completed successfully'
  }
}
```

## Error Handling

### Error Response Format
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  },
  "timestamp": "2025-01-31T12:00:00Z",
  "request_id": "uuid-v4"
}
```

### HTTP Status Codes

#### Success Codes
- `200 OK` - Successful GET, PUT, PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE

#### Client Error Codes
- `400 Bad Request` - Invalid request format
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `422 Unprocessable Entity` - Validation errors
- `429 Too Many Requests` - Rate limit exceeded

#### Server Error Codes
- `500 Internal Server Error` - Unexpected server error
- `502 Bad Gateway` - External service error
- `503 Service Unavailable` - Service temporarily unavailable
- `504 Gateway Timeout` - External service timeout

### Error Codes

#### Authentication Errors
- `AUTH_TOKEN_INVALID` - Invalid JWT token
- `AUTH_TOKEN_EXPIRED` - Expired JWT token
- `AUTH_CREDENTIALS_INVALID` - Invalid login credentials
- `AUTH_PERMISSIONS_INSUFFICIENT` - Insufficient permissions

#### Validation Errors
- `VALIDATION_ERROR` - General validation error
- `VALIDATION_REQUIRED_FIELD` - Required field missing
- `VALIDATION_FORMAT_INVALID` - Invalid field format
- `VALIDATION_VALUE_OUT_OF_RANGE` - Value outside allowed range

#### Resource Errors
- `RESOURCE_NOT_FOUND` - Requested resource not found
- `RESOURCE_ALREADY_EXISTS` - Resource already exists
- `RESOURCE_CONFLICT` - Resource state conflict
- `RESOURCE_LOCKED` - Resource is locked

#### External Service Errors
- `OCI_CONNECTION_ERROR` - OCI service unavailable
- `GENAI_SERVICE_ERROR` - AI service error
- `KUBERNETES_CONNECTION_ERROR` - Kubernetes cluster unreachable
- `NOTIFICATION_SEND_ERROR` - Notification delivery failed

## Rate Limiting

### Default Limits
- **Authenticated Users**: 1000 requests per hour
- **Admin Users**: 5000 requests per hour
- **Anonymous Users**: 100 requests per hour

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1706782800
X-RateLimit-Retry-After: 3600
```

### Rate Limit Response
```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Try again later.",
    "retry_after": 3600
  }
}
```

## SDK Examples

### Python SDK Example
```python
import requests
import json

class GenAICloudOpsClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })
    
    def login(self, email, password):
        response = self.session.post(
            f'{self.base_url}/api/v1/auth/login',
            json={'email': email, 'password': password}
        )
        if response.status_code == 200:
            token = response.json()['data']['access_token']
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
            return token
        else:
            raise Exception(f'Login failed: {response.text}')
    
    def get_resources(self, compartment_id=None):
        params = {}
        if compartment_id:
            params['compartment_id'] = compartment_id
        
        response = self.session.get(
            f'{self.base_url}/api/v1/monitoring/resources',
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def chat_with_ai(self, message, context=None):
        data = {'message': message}
        if context:
            data['context'] = context
        
        response = self.session.post(
            f'{self.base_url}/api/v1/genai/chat',
            json=data
        )
        response.raise_for_status()
        return response.json()

# Usage example
client = GenAICloudOpsClient('http://localhost:8000')
client.login('admin@example.com', 'password')

# Get resource status
resources = client.get_resources()
print(f"Found {len(resources['data']['resources'])} resources")

# Chat with AI
response = client.chat_with_ai(
    "What resources need attention?",
    context={'include_metrics': True}
)
print(response['data']['response'])
```

### JavaScript SDK Example
```javascript
class GenAICloudOpsClient {
  constructor(baseUrl, apiKey = null) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.apiKey) {
      headers.Authorization = `Bearer ${this.apiKey}`;
    }

    const response = await fetch(url, {
      ...options,
      headers
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async login(email, password) {
    const response = await this.request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });

    this.apiKey = response.data.access_token;
    return this.apiKey;
  }

  async getResources(compartmentId = null) {
    const params = new URLSearchParams();
    if (compartmentId) {
      params.append('compartment_id', compartmentId);
    }

    const endpoint = `/api/v1/monitoring/resources?${params}`;
    return this.request(endpoint);
  }

  async chatWithAI(message, context = null) {
    return this.request('/api/v1/genai/chat', {
      method: 'POST',
      body: JSON.stringify({ message, context })
    });
  }

  // WebSocket connection
  connectWebSocket() {
    const wsUrl = this.baseUrl.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/api/v1/ws/realtime`);

    ws.onopen = () => {
      // Authenticate WebSocket connection
      ws.send(JSON.stringify({
        type: 'auth',
        token: this.apiKey
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received:', data);
    };

    return ws;
  }
}

// Usage example
const client = new GenAICloudOpsClient('http://localhost:8000');

(async () => {
  try {
    await client.login('admin@example.com', 'password');
    
    const resources = await client.getResources();
    console.log(`Found ${resources.data.resources.length} resources`);

    const aiResponse = await client.chatWithAI(
      'Show me critical alerts',
      { include_metrics: true }
    );
    console.log(aiResponse.data.response);

    // Connect to real-time updates
    const ws = client.connectWebSocket();
    ws.send(JSON.stringify({
      type: 'subscribe',
      channels: ['alerts', 'metrics']
    }));

  } catch (error) {
    console.error('Error:', error);
  }
})();
```

### cURL Examples

#### Basic Authentication
```bash
# Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password"}' \
  | jq -r '.data.access_token')

echo "Token: $TOKEN"
```

#### Resource Monitoring
```bash
# Get all resources
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/monitoring/resources

# Get specific resource details
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/monitoring/resources/ocid1.instance.oc1..xxx

# Get resource metrics
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/monitoring/resources/ocid1.instance.oc1..xxx/metrics?resolution=5m&start_time=2025-01-31T10:00:00Z"
```

#### AI Interaction
```bash
# Chat with AI
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the health status of my infrastructure?"}' \
  http://localhost:8000/api/v1/genai/chat

# Generate analysis
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_type": "analysis",
    "data": {
      "resource_metrics": {"cpu_usage": 85.2},
      "alert_data": {"active_alerts": 3}
    }
  }' \
  http://localhost:8000/api/v1/genai/analyze
```

#### Remediation
```bash
# Submit remediation request
EXECUTION_ID=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "k8s_pod_restart",
    "context": {
      "pod_name": "frontend-deployment-xyz",
      "namespace": "production"
    }
  }' \
  http://localhost:8000/api/v1/remediation/submit \
  | jq -r '.data.execution_id')

# Approve remediation
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comments": "Approved for immediate execution"}' \
  http://localhost:8000/api/v1/remediation/approve/$EXECUTION_ID

# Check execution status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/remediation/executions/$EXECUTION_ID
```

For more examples and detailed integration guides, see the [Integration Examples](examples/) directory. 