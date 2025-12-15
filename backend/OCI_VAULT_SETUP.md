# OCI Vault Integration Setup Guide

This guide provides comprehensive instructions for setting up OCI Vault integration with the GenAI CloudOps platform.

## Prerequisites

### 1. OCI Resources Required

- **OCI Vault**: Create a vault in your OCI tenancy
- **KMS Key**: Create or use existing KMS key for encryption
- **Compartment**: Identify the compartment for storing secrets
- **IAM Policies**: Configure appropriate policies for vault access

### 2. OCI CLI and Authentication

Ensure you have:
- OCI CLI installed and configured
- Valid OCI configuration file (`~/.oci/config`)
- API signing key pair

## Step 1: Create OCI Vault Resources

### Create a Vault

```bash
# Create a vault
oci kms management vault create \
  --compartment-id <compartment-ocid> \
  --display-name "genai-cloudops-vault" \
  --vault-type DEFAULT

# Note the vault OCID from the response
```

### Create KMS Key

```bash
# Create a master encryption key
oci kms management key create \
  --compartment-id <compartment-ocid> \
  --display-name "genai-cloudops-master-key" \
  --key-shape '{"algorithm": "AES", "length": 32}' \
  --endpoint <vault-management-endpoint>

# Note the key OCID from the response
```

## Step 2: Configure IAM Policies

### For Development (User-based Access)

```bash
# Create a policy for vault access
oci iam policy create \
  --compartment-id <tenancy-ocid> \
  --name "genai-cloudops-vault-policy" \
  --description "Vault access for GenAI CloudOps" \
  --statements '[
    "Allow group genai-cloudops-developers to manage secret-family in compartment <compartment-name>",
    "Allow group genai-cloudops-developers to use vaults in compartment <compartment-name>",
    "Allow group genai-cloudops-developers to use keys in compartment <compartment-name>"
  ]'
```

### For Production (Instance Principal)

```bash
# Create dynamic group for OKE workers
oci iam dynamic-group create \
  --name "genai-cloudops-oke-workers" \
  --description "OKE worker nodes for GenAI CloudOps" \
  --matching-rule "ALL {instance.compartment.id = '<oke-compartment-ocid>'}"

# Create policy for instance principals
oci iam policy create \
  --compartment-id <tenancy-ocid> \
  --name "genai-cloudops-vault-instance-policy" \
  --description "Instance principal vault access" \
  --statements '[
    "Allow dynamic-group genai-cloudops-oke-workers to manage secret-family in compartment <compartment-name>",
    "Allow dynamic-group genai-cloudops-oke-workers to use vaults in compartment <compartment-name>",
    "Allow dynamic-group genai-cloudops-oke-workers to use keys in compartment <compartment-name>"
  ]'
```

## Step 3: Store Initial Secrets

### Using OCI CLI

```bash
# Store database password
oci secrets secret create-base64 \
  --compartment-id <compartment-ocid> \
  --vault-id <vault-ocid> \
  --key-id <key-ocid> \
  --secret-name "database_password" \
  --secret-content-content $(echo -n "your-secure-db-password" | base64)

# Store JWT secret
oci secrets secret create-base64 \
  --compartment-id <compartment-ocid> \
  --vault-id <vault-ocid> \
  --key-id <key-ocid> \
  --secret-name "jwt_secret_key" \
  --secret-content-content $(echo -n "your-jwt-secret-key" | base64)

# Store Groq API key
oci secrets secret create-base64 \
  --compartment-id <compartment-ocid> \
  --vault-id <vault-ocid> \
  --key-id <key-ocid> \
  --secret-name "groq_api_key" \
  --secret-content-content $(echo -n "your-groq-api-key" | base64)
```

### Using the API (after deployment)

```bash
# Store API key via the GenAI CloudOps API
curl -X POST "https://your-domain.com/api/v1/vault/api-keys" \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "groq",
    "api_key": "your-groq-api-key",
    "description": "Groq API key for GenAI services"
  }'
```

## Step 4: Configure Application

### Environment Variables

```bash
# Required environment variables
export OCI_VAULT_ENABLED=true
export OCI_COMPARTMENT_ID=<compartment-ocid>
export OCI_VAULT_ID=<vault-ocid>
export OCI_KMS_KEY_ID=<key-ocid>

# For development
export OCI_USE_INSTANCE_PRINCIPAL=false

# For production (OKE)
export OCI_USE_INSTANCE_PRINCIPAL=true
```

### Helm Values Configuration

#### Development (`values-dev.yaml`)

```yaml
oci:
  vault:
    enabled: true
    vaultId: "ocid1.vault.oc1.region...."
    compartmentId: "ocid1.compartment.oc1...."
    kmsKeyId: "ocid1.key.oc1.region...."
    useInstancePrincipal: false
    cacheTtlMinutes: 15
```

#### Production (`values-prod.yaml`)

```yaml
oci:
  vault:
    enabled: true
    vaultId: "ocid1.vault.oc1.region...."
    compartmentId: "ocid1.compartment.oc1...."
    kmsKeyId: "ocid1.key.oc1.region...."
    useInstancePrincipal: true
    cacheTtlMinutes: 10
```

## Step 5: Deploy with Vault Integration

### Development Deployment

```bash
helm install genai-cloudops ./deployment/helm-chart \
  --namespace genai-cloudops \
  --values ./deployment/helm-chart/values-dev.yaml \
  --set oci.vault.vaultId="<vault-ocid>" \
  --set oci.vault.compartmentId="<compartment-ocid>" \
  --set oci.vault.kmsKeyId="<key-ocid>"
```

### Production Deployment

```bash
helm install genai-cloudops ./deployment/helm-chart \
  --namespace genai-cloudops \
  --values ./deployment/helm-chart/values-prod.yaml \
  --set oci.vault.vaultId="<vault-ocid>" \
  --set oci.vault.compartmentId="<compartment-ocid>" \
  --set oci.vault.kmsKeyId="<key-ocid>"
```

## Step 6: Verify Vault Integration

### Check Vault Health

```bash
# Check vault health endpoint
curl -X GET "https://your-domain.com/api/v1/vault/health" \
  -H "Authorization: Bearer <token>"
```

### List Secrets (Admin Only)

```bash
# List all secrets
curl -X GET "https://your-domain.com/api/v1/vault/secrets" \
  -H "Authorization: Bearer <admin-token>"
```

### Get Vault Statistics

```bash
# Get vault statistics
curl -X GET "https://your-domain.com/api/v1/vault/stats" \
  -H "Authorization: Bearer <admin-token>"
```

## Secret Management Operations

### Store a New Secret

```bash
curl -X POST "https://your-domain.com/api/v1/vault/secrets" \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_secret",
    "value": "secret-value",
    "secret_type": "generic",
    "description": "My secret description",
    "tags": {"environment": "production"}
  }'
```

### Rotate a Secret

```bash
curl -X PUT "https://your-domain.com/api/v1/vault/secrets/my_secret/rotate" \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "value": "new-secret-value"
  }'
```

### Rotate JWT Secret

```bash
curl -X POST "https://your-domain.com/api/v1/vault/jwt-secret/rotate" \
  -H "Authorization: Bearer <admin-token>"
```

## Security Best Practices

### 1. Access Control

- Use principle of least privilege
- Implement regular access reviews
- Use dynamic groups for OKE workloads
- Separate development and production vaults

### 2. Secret Rotation

- Implement regular secret rotation schedules
- Use versioning for graceful transitions
- Monitor secret access patterns
- Set up alerts for unusual access

### 3. Monitoring and Auditing

- Enable OCI audit logging
- Monitor vault access patterns
- Set up alerts for failed access attempts
- Regular security assessments

### 4. Backup and Recovery

- Use OCI vault's built-in durability
- Document secret recovery procedures
- Test recovery processes regularly
- Maintain encrypted backups of critical secrets

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

```bash
# Check OCI configuration
oci setup config

# Verify compartment access
oci iam compartment get --compartment-id <compartment-ocid>
```

#### 2. Permission Errors

```bash
# List policies affecting user/group
oci iam policy list --compartment-id <tenancy-ocid>

# Check dynamic group membership
oci iam dynamic-group get --dynamic-group-id <dynamic-group-ocid>
```

#### 3. Secret Not Found

```bash
# List secrets in compartment
oci secrets secret list --compartment-id <compartment-ocid>

# Check secret lifecycle state
oci secrets secret get --secret-id <secret-ocid>
```

#### 4. Cache Issues

```bash
# Clear application cache
curl -X POST "https://your-domain.com/api/v1/vault/cache/clear" \
  -H "Authorization: Bearer <admin-token>"
```

### Logging and Debugging

#### Enable Debug Logging

```yaml
# In values.yaml
backend:
  config:
    debug: "true"
```

#### Check Application Logs

```bash
# Check backend logs
kubectl logs -l app.kubernetes.io/component=backend -n genai-cloudops

# Check for vault-specific errors
kubectl logs -l app.kubernetes.io/component=backend -n genai-cloudops | grep -i vault
```

## Monitoring and Alerts

### Recommended Metrics

- Secret retrieval success/failure rates
- Cache hit/miss ratios
- Secret rotation frequency
- Access pattern anomalies

### Alert Configuration

```yaml
# Example Prometheus alert
- alert: VaultSecretFailure
  expr: vault_secret_retrieval_failures_total > 5
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: High vault secret retrieval failure rate
```

## Maintenance and Operations

### Regular Tasks

1. **Monthly**: Review secret access logs
2. **Quarterly**: Rotate critical secrets
3. **Annually**: Review IAM policies and access
4. **As needed**: Update vault configuration

### Backup Procedures

```bash
# Export secret metadata (not values)
oci secrets secret list --compartment-id <compartment-ocid> \
  --output table > secrets_inventory.txt

# Document secret relationships
kubectl get configmaps -n genai-cloudops -o yaml > configmaps_backup.yaml
```

This completes the OCI Vault integration setup. The vault service provides enterprise-grade secret management with encryption at rest, access controls, and audit logging. 