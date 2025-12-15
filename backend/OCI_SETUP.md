# OCI SDK Authentication Setup Guide

This guide explains how to set up OCI authentication for the GenAI CloudOps backend service.

## Prerequisites

1. **OCI Account**: You need an active Oracle Cloud Infrastructure account
2. **API Key**: Generate an API key pair for authentication
3. **Permissions**: Ensure your user has the necessary IAM policies

## Setup Methods

### Method 1: OCI Config File (Recommended for Development)

#### Step 1: Install OCI CLI
```bash
# Install OCI CLI
pip install oci-cli

# Configure OCI CLI (this will create the config file)
oci setup config
```

#### Step 2: Verify Configuration
The setup will create a config file at `~/.oci/config` with content like:
```ini
[DEFAULT]
user=ocid1.user.oc1..your-user-id
fingerprint=your-key-fingerprint
tenancy=ocid1.tenancy.oc1..your-tenancy-id
region=us-phoenix-1
key_file=~/.oci/oci_api_key.pem
```

#### Step 3: Set Environment Variables
```bash
export OCI_CONFIG_FILE=~/.oci/config
export OCI_PROFILE=DEFAULT
export OCI_REGION=us-phoenix-1
```

### Method 2: Environment Variables (Recommended for Production)

#### Step 1: Generate API Key
1. Log in to OCI Console
2. Go to **Identity & Security** > **Users**
3. Select your user
4. Click **API Keys** > **Add API Key**
5. Download the private key and note the fingerprint

#### Step 2: Set Environment Variables
```bash
export OCI_TENANCY_ID=ocid1.tenancy.oc1..your-tenancy-id
export OCI_USER_ID=ocid1.user.oc1..your-user-id
export OCI_FINGERPRINT=your-key-fingerprint
export OCI_KEY_FILE=/path/to/your/private-key.pem
export OCI_REGION=us-phoenix-1
```

#### Step 3: For Docker/Kubernetes Deployment
Create a Kubernetes secret or Docker environment file:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: oci-credentials
type: Opaque
stringData:
  OCI_TENANCY_ID: "ocid1.tenancy.oc1..your-tenancy-id"
  OCI_USER_ID: "ocid1.user.oc1..your-user-id"
  OCI_FINGERPRINT: "your-key-fingerprint"
  OCI_KEY_FILE: "/etc/oci/key.pem"
  OCI_REGION: "us-phoenix-1"
```

## Required IAM Policies

Your user or group needs the following IAM policies:

### Minimum Required Policies
```
Allow group CloudOpsUsers to read all-resources in tenancy
Allow group CloudOpsUsers to read metrics in tenancy
Allow group CloudOpsUsers to read compartments in tenancy
```

### Recommended Policies for Full Functionality
```
Allow group CloudOpsUsers to read all-resources in tenancy
Allow group CloudOpsUsers to read metrics in tenancy  
Allow group CloudOpsUsers to read compartments in tenancy
Allow group CloudOpsUsers to read instances in tenancy
Allow group CloudOpsUsers to read autonomous-databases in tenancy
Allow group CloudOpsUsers to read clusters in tenancy
Allow group CloudOpsUsers to read gateways in tenancy
Allow group CloudOpsUsers to read load-balancers in tenancy
Allow group CloudOpsUsers to read virtual-network-family in tenancy
```

### For Resource Management (Operator/Admin roles)
```
Allow group CloudOpsOperators to manage instances in tenancy
Allow group CloudOpsOperators to manage autonomous-databases in tenancy
Allow group CloudOpsOperators to manage clusters in tenancy
```

## Supported OCI Services

The GenAI CloudOps platform integrates with the following OCI services:

### Core Services
- **Compute**: Virtual machines and bare metal instances
- **Storage**: Block volumes and object storage
- **Networking**: VCNs, subnets, security lists

### Database Services  
- **Autonomous Database**: Oracle Autonomous Database instances
- **MySQL Database Service**: Managed MySQL instances
- **Database Systems**: Oracle Database systems

### Container Services
- **OKE (Oracle Kubernetes Engine)**: Managed Kubernetes clusters
- **Container Registry**: Docker image registry

### Application Services
- **API Gateway**: Managed API gateway service
- **Load Balancer**: Layer 4 and Layer 7 load balancers
- **Functions**: Serverless compute service

### Monitoring & Security
- **Monitoring**: CloudWatch-style metrics and monitoring
- **Logging**: Centralized logging service
- **Security**: Security zones and cloud guard

## Testing the Setup

### Test OCI Connectivity
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Test OCI connection
python -c "
import asyncio
from app.services.cloud_service import oci_service

async def test():
    try:
        compartments = await oci_service.get_compartments()
        print(f'Success! Found {len(compartments)} compartments')
        for comp in compartments:
            print(f'  - {comp[\"name\"]} ({comp[\"id\"]})')
    except Exception as e:
        print(f'Error: {e}')

asyncio.run(test())
"
```

### Test API Endpoints
```bash
# Start the backend server
uvicorn main:app --reload

# Test compartments endpoint (requires authentication)
curl -X GET "http://localhost:8000/api/v1/cloud/compartments" \
  -H "Authorization: Bearer your-jwt-token"
```

## Troubleshooting

### Common Issues

#### 1. "Config file not found"
- **Problem**: OCI config file doesn't exist
- **Solution**: Run `oci setup config` or use environment variables

#### 2. "Invalid fingerprint"
- **Problem**: API key fingerprint doesn't match
- **Solution**: Regenerate API key or verify fingerprint in OCI console

#### 3. "Insufficient permissions"
- **Problem**: User lacks required IAM policies
- **Solution**: Add the required policies listed above

#### 4. "Service not available in region"
- **Problem**: Trying to access a service not available in your region
- **Solution**: Switch to a region that supports the service

#### 5. "Rate limit exceeded"
- **Problem**: Too many API calls
- **Solution**: The service includes automatic retry logic and caching

### Debug Mode
Enable debug logging to troubleshoot issues:
```bash
export LOG_LEVEL=DEBUG
uvicorn main:app --reload
```

### Mock Mode for Development
If you don't have OCI access, the service will automatically fall back to mock data:
```python
# The service detects missing OCI credentials and provides mock responses
# This allows development without OCI access
```

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use IAM policies** with least privilege principle
3. **Rotate API keys** regularly (every 90 days)
4. **Use separate accounts** for development and production
5. **Enable MFA** on your OCI account
6. **Monitor API usage** through OCI audit logs

## Support

For issues related to:
- **OCI SDK**: [Oracle Cloud Infrastructure SDK Documentation](https://docs.oracle.com/en-us/iaas/tools/python/latest/)
- **OCI IAM**: [Identity and Access Management](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/overview.htm)
- **GenAI CloudOps**: Check the application logs or create an issue 