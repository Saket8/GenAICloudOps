# GenAI CloudOps Helm Chart

This Helm chart deploys the GenAI CloudOps platform on Oracle Kubernetes Engine (OKE) with comprehensive production-ready configurations.

## Prerequisites

- Kubernetes 1.23+
- Helm 3.0+
- Oracle Kubernetes Engine (OKE) cluster
- kubectl configured for your cluster
- (Optional) cert-manager for TLS certificates
- (Optional) Prometheus Operator for monitoring

## Quick Start

### 1. Add Required Helm Repositories (if using external dependencies)

```bash
# For ingress-nginx
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx

# For cert-manager (optional)
helm repo add jetstack https://charts.jetstack.io

# For monitoring (optional)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

helm repo update
```

### 2. Install Dependencies

```bash
# Install ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace

# Install cert-manager (optional, for TLS)
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Install Prometheus (optional, for monitoring)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### 3. Create Secrets

Before deploying, create necessary secrets:

```bash
# Create namespace
kubectl create namespace genai-cloudops

# Create PostgreSQL password secret
kubectl create secret generic genai-cloudops-secrets \
  --from-literal=postgres-password="your-secure-password" \
  --from-literal=secret-key="your-jwt-secret-key" \
  --from-literal=groq-api-key="your-groq-api-key" \
  --namespace genai-cloudops

# Create OCI configuration secret (if using OCI integration)
kubectl create secret generic genai-cloudops-oci-config \
  --from-file=config=/path/to/your/oci/config \
  --from-file=key.pem=/path/to/your/oci/private-key.pem \
  --namespace genai-cloudops
```

### 4. Deploy the Application

#### Development Environment
```bash
helm install genai-cloudops ./deployment/helm-chart \
  --namespace genai-cloudops \
  --values ./deployment/helm-chart/values-dev.yaml
```

#### Staging Environment
```bash
helm install genai-cloudops ./deployment/helm-chart \
  --namespace genai-cloudops \
  --values ./deployment/helm-chart/values-staging.yaml \
  --set genai.groqApiKey="your-groq-api-key" \
  --set postgres.password="your-secure-password"
```

#### Production Environment
```bash
helm install genai-cloudops ./deployment/helm-chart \
  --namespace genai-cloudops \
  --values ./deployment/helm-chart/values-prod.yaml \
  --set genai.groqApiKey="your-groq-api-key" \
  --set postgres.password="your-secure-password" \
  --set backend.secretKey="your-jwt-secret-key" \
  --set ingress.hosts[0].host="your-domain.com"
```

## Configuration

### Core Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `frontend.image.repository` | Frontend image repository | `ghcr.io/your-org/genai-cloudops-frontend` |
| `frontend.image.tag` | Frontend image tag | `latest` |
| `backend.image.repository` | Backend image repository | `ghcr.io/your-org/genai-cloudops-backend` |
| `backend.image.tag` | Backend image tag | `latest` |

### Database Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgres.enabled` | Enable PostgreSQL | `true` |
| `postgres.persistence.enabled` | Enable persistent storage | `true` |
| `postgres.persistence.size` | Storage size | `20Gi` |
| `postgres.persistence.storageClass` | Storage class | `""` |

### OCI Integration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `oci.enabled` | Enable OCI integration | `true` |
| `oci.region` | OCI region | `us-ashburn-1` |
| `oci.tenancyId` | OCI tenancy OCID | `""` |
| `oci.userId` | OCI user OCID | `""` |

### GenAI Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `genai.groqApiKey` | Groq API key | `""` |
| `genai.groqModel` | Groq model | `llama3-8b-8192` |
| `genai.rateLimitPerMinute` | Rate limit per minute | `100` |

### Ingress Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class | `nginx` |
| `ingress.hosts[0].host` | Hostname | `genai-cloudops.local` |

### Autoscaling Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `autoscaling.enabled` | Enable HPA | `false` |
| `autoscaling.minReplicas` | Minimum replicas | `1` |
| `autoscaling.maxReplicas` | Maximum replicas | `10` |
| `autoscaling.targetCPUUtilizationPercentage` | CPU target | `70` |

### Monitoring Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `monitoring.enabled` | Enable monitoring | `false` |
| `monitoring.prometheus.enabled` | Enable Prometheus | `false` |
| `monitoring.prometheusRule.enabled` | Enable alert rules | `false` |

## Environment-Specific Deployments

### Development
- Single replica
- Ephemeral storage
- Debug mode enabled
- Local domain names

### Staging
- Multiple replicas
- Persistent storage
- SSL/TLS enabled
- Monitoring enabled
- Network policies

### Production
- High availability setup
- Autoscaling enabled
- Security hardening
- Full monitoring stack
- Pod disruption budgets
- Anti-affinity rules

## OCI-Specific Features

### OCI Load Balancer Integration

```yaml
ingress:
  oci:
    loadBalancer:
      enabled: true
      shape: "flexible"
      flexMin: "100"
      flexMax: "8000"
      subnet1: "ocid1.subnet.oc1.region.aaaaaa"
      subnet2: "ocid1.subnet.oc1.region.bbbbbb"
```

### OCI Block Storage

```yaml
postgres:
  persistence:
    storageClass: "oci-bv"  # OCI Block Volume
    size: 50Gi
```

## Security Considerations

### RBAC
- ServiceAccount with minimal required permissions
- Role-based access control
- Optional cluster-wide permissions

### Network Policies
- Ingress and egress restrictions
- Service-to-service communication control
- External API access limitations

### Pod Security
- Non-root user execution
- Read-only root filesystem
- Capability dropping
- Security contexts

## Monitoring and Observability

### Prometheus Integration
- ServiceMonitor for metrics collection
- Custom alerting rules
- Performance monitoring

### Grafana Dashboards
- Pre-configured dashboards
- Request rate monitoring
- Resource utilization tracking

### Alerting Rules
- High error rate alerts
- Response time monitoring
- Resource usage alerts
- Database connectivity monitoring

## Troubleshooting

### Common Issues

1. **Pod startup failures**
   ```bash
   kubectl describe pod -l app.kubernetes.io/name=genai-cloudops -n genai-cloudops
   ```

2. **Database connection issues**
   ```bash
   kubectl logs -l app.kubernetes.io/component=backend -n genai-cloudops
   ```

3. **Ingress not working**
   ```bash
   kubectl get ingress -n genai-cloudops
   kubectl describe ingress genai-cloudops-ingress -n genai-cloudops
   ```

### Debugging Commands

```bash
# Check all resources
kubectl get all -n genai-cloudops

# Check secrets
kubectl get secrets -n genai-cloudops

# Check configmaps
kubectl get configmaps -n genai-cloudops

# Check events
kubectl get events -n genai-cloudops --sort-by='.firstTimestamp'

# Port forward for testing
kubectl port-forward service/genai-cloudops-frontend 8080:80 -n genai-cloudops
kubectl port-forward service/genai-cloudops-backend 8000:8000 -n genai-cloudops
```

## Upgrading

### Helm Upgrades

```bash
# Upgrade with new values
helm upgrade genai-cloudops ./deployment/helm-chart \
  --namespace genai-cloudops \
  --values ./deployment/helm-chart/values-prod.yaml

# Check upgrade status
helm status genai-cloudops -n genai-cloudops

# Rollback if needed
helm rollback genai-cloudops 1 -n genai-cloudops
```

### Database Migrations

The application handles database migrations automatically on startup. For manual migrations:

```bash
kubectl exec -it deployment/genai-cloudops-backend -n genai-cloudops -- python -m alembic upgrade head
```

## Backup and Recovery

### Database Backup

```bash
# Create database backup
kubectl exec -it deployment/genai-cloudops-postgres -n genai-cloudops -- \
  pg_dump -h localhost -U postgres genai_cloudops > backup.sql

# Restore database
kubectl exec -i deployment/genai-cloudops-postgres -n genai-cloudops -- \
  psql -h localhost -U postgres genai_cloudops < backup.sql
```

### Persistent Volume Backup

Follow OCI Block Volume backup procedures for persistent storage.

## Contributing

1. Make changes to templates in `deployment/helm-chart/templates/`
2. Update values in `deployment/helm-chart/values.yaml`
3. Test with `helm template` and `helm lint`
4. Update environment-specific values files as needed

## Support

For issues and questions:
- Check the troubleshooting section
- Review Kubernetes events and logs
- Consult OCI OKE documentation
- Review Helm chart templates 