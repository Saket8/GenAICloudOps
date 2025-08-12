# Enabling Live OCI and Kubernetes Integrations

This project defaults to SAFE dummy mode for all external connections (OCI SDK and Kubernetes kubeconfig). Follow this guide to switch to live integrations.

## 1) Configuration Flags

The following flags live in `backend/app/core/config.py` and can be overridden by environment variables (preferred for deployments):

- `USE_DUMMY_OCI` (default: `True`) — when `False`, the backend initializes real OCI SDK clients and performs live API calls.
- `USE_DUMMY_KUBERNETES` (default: `True`) — when `False`, the backend uses real kubeconfig and Kubernetes clients.
- `USE_DUMMY_VAULT` (default: `True`) — when `False`, the backend uses live OCI Vault and KMS clients.

You can set these in your environment or `.env` file:

```
USE_DUMMY_OCI=False
USE_DUMMY_KUBERNETES=False
USE_DUMMY_VAULT=False
```

Restart the backend after changes.

## 2) Live OCI Setup

Provide OCI credentials via either a config file or environment variables.

### Option A: `~/.oci/config`
- Create `~/.oci/config` with a profile (default `DEFAULT`):
```
[DEFAULT]
user=ocid1.user.oc1..aaaa...
fingerprint=aa:bb:cc:dd:...
tenancy=ocid1.tenancy.oc1..aaaa...
region=eu-frankfurt-1
key_file=/path/to/oci_api_key.pem
```
- Ensure `key_file` is readable by the backend process.
- Optionally set environment variables:
```
OCI_CONFIG_FILE=/home/youruser/.oci/config
OCI_PROFILE=DEFAULT
```

### Option B: Environment variables
```
OCI_TENANCY_ID=ocid1.tenancy.oc1..aaaa...
OCI_USER_ID=ocid1.user.oc1..aaaa...
OCI_FINGERPRINT=aa:bb:cc:dd:...
OCI_KEY_FILE=/path/to/oci_api_key.pem
OCI_REGION=eu-frankfurt-1
```

### Vault (optional)
If using OCI Vault, also set:
```
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..aaaa...
OCI_VAULT_ID=ocid1.vault.oc1..aaaa...
OCI_KMS_KEY_ID=ocid1.key.oc1..aaaa...
USE_DUMMY_VAULT=False
```

## 3) Live Kubernetes Setup

Set `USE_DUMMY_KUBERNETES=False` and provide a kubeconfig.

- Via API: POST to `/api/v1/kubernetes/configure-cluster` with `kubeconfig_content` and `cluster_name`.
- Or load the default kubeconfig from disk (the service attempts auto-config when needed).

Example request body:
```
{
  "kubeconfig_content": "<contents of your kubeconfig>",
  "cluster_name": "production"
}
```

## 4) Verifying Live Connections

- OCI: Call endpoints that list compartments/resources (e.g., cost analyzer or cloud resources). Logs should show real OCI client initialization.
- Kubernetes: Call `/api/v1/kubernetes/health` and `/api/v1/kubernetes/cluster-info`.
- Vault: Attempt to retrieve a secret via the service that uses `OCIVaultService`.

## 5) Troubleshooting

- Ensure network egress is allowed to OCI endpoints.
- Verify file permissions for `oci_api_key.pem`.
- Double-check region, tenancy, user OCIDs, and fingerprint values.
- Check application logs for initialization or API errors.

## 6) Reverting to Dummy Mode

To safely disable all live calls, set:
```
USE_DUMMY_OCI=True
USE_DUMMY_KUBERNETES=True
USE_DUMMY_VAULT=True
```
Then restart the backend. 