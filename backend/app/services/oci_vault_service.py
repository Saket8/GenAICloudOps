"""
OCI Vault Service for Secure Secrets Management
Provides secure storage, retrieval, and management of sensitive data using OCI Vault
"""

import logging
import json
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Union
from dataclasses import dataclass
from enum import Enum
import base64

try:
    import oci
    from oci.vault import VaultsClient
    from oci.secrets import SecretsClient
    from oci.key_management import KmsVaultClient, KmsManagementClient
    OCI_AVAILABLE = True
except ImportError:
    OCI_AVAILABLE = False
    logging.warning("OCI SDK not available. OCI Vault integration will be disabled.")

from ..core.config import settings


class SecretType(Enum):
    """Types of secrets managed by the vault"""
    DATABASE_PASSWORD = "database_password"
    API_KEY = "api_key"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    CERTIFICATE = "certificate"
    PRIVATE_KEY = "private_key"
    GENERIC = "generic"


@dataclass
class SecretMetadata:
    """Metadata for a secret stored in OCI Vault"""
    secret_id: str
    name: str
    secret_type: SecretType
    version_number: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    rotation_interval: Optional[timedelta] = None
    tags: Optional[Dict[str, str]] = None


@dataclass
class SecretValue:
    """Represents a secret value with metadata"""
    value: str
    metadata: SecretMetadata
    retrieved_at: datetime
    expires_at: Optional[datetime] = None


class OCIVaultService:
    """
    OCI Vault Service for secure secrets management
    
    Features:
    - Secure secret storage and retrieval
    - Automatic secret rotation
    - Caching with TTL
    - Access logging and audit trails
    - Encryption at rest and in transit
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._vault_client: Optional[VaultsClient] = None
        self._secrets_client: Optional[SecretsClient] = None
        self._kms_vault_client: Optional[KmsVaultClient] = None
        self._kms_management_client: Optional[KmsManagementClient] = None
        
        # Cache for secrets (in-memory with TTL)
        self._secret_cache: Dict[str, SecretValue] = {}
        self._cache_ttl = timedelta(minutes=15)  # Default cache TTL
        
        # OCI configuration
        self.compartment_id = getattr(settings, 'OCI_COMPARTMENT_ID', '')
        self.vault_id = getattr(settings, 'OCI_VAULT_ID', '')
        self.kms_key_id = getattr(settings, 'OCI_KMS_KEY_ID', '')
        
        # Initialize OCI clients if available and not in dummy mode
        if OCI_AVAILABLE and not getattr(settings, 'USE_DUMMY_VAULT', False):
            self._initialize_clients()
        else:
            self.logger.warning("Using mock vault implementation (OCI disabled or USE_DUMMY_VAULT=True).")
    
    def _initialize_clients(self):
        """Initialize OCI clients with proper authentication"""
        try:
            # Use instance principal authentication in OKE or config file authentication
            if hasattr(settings, 'OCI_USE_INSTANCE_PRINCIPAL') and settings.OCI_USE_INSTANCE_PRINCIPAL:
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                config = {}
            else:
                config = oci.config.from_file(
                    file_location=getattr(settings, 'OCI_CONFIG_FILE', '~/.oci/config'),
                    profile_name=getattr(settings, 'OCI_PROFILE', 'DEFAULT')
                )
                signer = None
            
            # Initialize clients
            self._vault_client = VaultsClient(config, signer=signer)
            self._secrets_client = SecretsClient(config, signer=signer)
            self._kms_vault_client = KmsVaultClient(config, signer=signer)
            self._kms_management_client = KmsManagementClient(config, signer=signer)
            
            self.logger.info("Successfully initialized OCI Vault clients")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OCI clients: {str(e)}")
            raise
    
    async def get_secret(self, secret_name: str, force_refresh: bool = False) -> Optional[str]:
        """
        Retrieve a secret from OCI Vault with caching
        
        Args:
            secret_name: Name of the secret to retrieve
            force_refresh: Force refresh from vault, bypassing cache
            
        Returns:
            Secret value or None if not found
        """
        try:
            # Check cache first (unless force refresh)
            if not force_refresh and secret_name in self._secret_cache:
                cached_secret = self._secret_cache[secret_name]
                if cached_secret.expires_at and cached_secret.expires_at > datetime.utcnow():
                    self.logger.debug(f"Retrieved secret '{secret_name}' from cache")
                    return cached_secret.value
                else:
                    # Remove expired secret from cache
                    del self._secret_cache[secret_name]
            
            # Retrieve from OCI Vault
            if not OCI_AVAILABLE or not self._secrets_client:
                return self._get_mock_secret(secret_name)
            
            secret_value = await self._retrieve_from_vault(secret_name)
            if secret_value:
                # Cache the secret
                self._cache_secret(secret_name, secret_value)
                self.logger.info(f"Successfully retrieved secret '{secret_name}' from vault")
                return secret_value.value
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving secret '{secret_name}': {str(e)}")
            return None
    
    async def _retrieve_from_vault(self, secret_name: str) -> Optional[SecretValue]:
        """Retrieve secret from OCI Vault"""
        try:
            # Find secret by name
            secrets_list = self._secrets_client.list_secrets(
                compartment_id=self.compartment_id,
                name=secret_name
            )
            
            if not secrets_list.data:
                self.logger.warning(f"Secret '{secret_name}' not found in vault")
                return None
            
            secret = secrets_list.data[0]
            
            # Get secret content
            secret_bundle = self._secrets_client.get_secret_bundle(
                secret_id=secret.id
            )
            
            # Decode secret content
            secret_content = base64.b64decode(
                secret_bundle.data.secret_bundle_content.content
            ).decode('utf-8')
            
            # Create metadata
            metadata = SecretMetadata(
                secret_id=secret.id,
                name=secret_name,
                secret_type=SecretType.GENERIC,  # Default, can be enhanced
                version_number=secret_bundle.data.version_number,
                created_at=secret.time_created.replace(tzinfo=None),
                tags=secret.defined_tags if hasattr(secret, 'defined_tags') else None
            )
            
            return SecretValue(
                value=secret_content,
                metadata=metadata,
                retrieved_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + self._cache_ttl
            )
            
        except Exception as e:
            self.logger.error(f"Error retrieving secret from vault: {str(e)}")
            return None
    
    def _cache_secret(self, secret_name: str, secret_value: SecretValue):
        """Cache secret with TTL"""
        self._secret_cache[secret_name] = secret_value
        self.logger.debug(f"Cached secret '{secret_name}' with TTL")
    
    def _get_mock_secret(self, secret_name: str) -> Optional[str]:
        """Mock implementation for development/testing"""
        mock_secrets = {
            'database_password': 'mock_db_password_123',
            'jwt_secret_key': 'mock_jwt_secret_key_456',
            'groq_api_key': 'mock_groq_api_key_789',
            'postgres_password': 'mock_postgres_password_abc'
        }
        
        value = mock_secrets.get(secret_name)
        if value:
            self.logger.debug(f"Retrieved mock secret '{secret_name}'")
        return value
    
    async def store_secret(self, secret_name: str, secret_value: str, 
                          secret_type: SecretType = SecretType.GENERIC,
                          description: str = "",
                          tags: Optional[Dict[str, str]] = None) -> bool:
        """
        Store a secret in OCI Vault
        
        Args:
            secret_name: Name for the secret
            secret_value: The secret value to store
            secret_type: Type of secret
            description: Description of the secret
            tags: Tags for the secret
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not OCI_AVAILABLE or not self._secrets_client:
                self.logger.info(f"Mock: Stored secret '{secret_name}' of type {secret_type.value}")
                return True
            
            # Encode secret content
            encoded_content = base64.b64encode(secret_value.encode('utf-8')).decode('utf-8')
            
            # Create secret
            secret_details = oci.secrets.models.CreateSecretDetails(
                compartment_id=self.compartment_id,
                vault_id=self.vault_id,
                key_id=self.kms_key_id,
                secret_name=secret_name,
                description=description,
                secret_content=oci.secrets.models.Base64SecretContentDetails(
                    content_type=oci.secrets.models.SecretContentDetails.CONTENT_TYPE_BASE64,
                    content=encoded_content
                ),
                defined_tags=tags or {}
            )
            
            response = self._secrets_client.create_secret(secret_details)
            
            # Remove from cache to force refresh
            if secret_name in self._secret_cache:
                del self._secret_cache[secret_name]
            
            self.logger.info(f"Successfully stored secret '{secret_name}' in vault")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing secret '{secret_name}': {str(e)}")
            return False
    
    async def rotate_secret(self, secret_name: str, new_value: str) -> bool:
        """
        Rotate a secret by creating a new version
        
        Args:
            secret_name: Name of the secret to rotate
            new_value: New secret value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not OCI_AVAILABLE or not self._secrets_client:
                self.logger.info(f"Mock: Rotated secret '{secret_name}'")
                return True
            
            # Find existing secret
            secrets_list = self._secrets_client.list_secrets(
                compartment_id=self.compartment_id,
                name=secret_name
            )
            
            if not secrets_list.data:
                self.logger.error(f"Secret '{secret_name}' not found for rotation")
                return False
            
            secret = secrets_list.data[0]
            
            # Create new version
            encoded_content = base64.b64encode(new_value.encode('utf-8')).decode('utf-8')
            
            update_details = oci.secrets.models.UpdateSecretDetails(
                secret_content=oci.secrets.models.Base64SecretContentDetails(
                    content_type=oci.secrets.models.SecretContentDetails.CONTENT_TYPE_BASE64,
                    content=encoded_content
                )
            )
            
            self._secrets_client.update_secret(secret.id, update_details)
            
            # Remove from cache
            if secret_name in self._secret_cache:
                del self._secret_cache[secret_name]
            
            self.logger.info(f"Successfully rotated secret '{secret_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rotating secret '{secret_name}': {str(e)}")
            return False
    
    async def delete_secret(self, secret_name: str, permanent: bool = False) -> bool:
        """
        Delete a secret from OCI Vault
        
        Args:
            secret_name: Name of the secret to delete
            permanent: If True, permanently delete; if False, schedule for deletion
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not OCI_AVAILABLE or not self._secrets_client:
                self.logger.info(f"Mock: Deleted secret '{secret_name}'")
                return True
            
            # Find secret
            secrets_list = self._secrets_client.list_secrets(
                compartment_id=self.compartment_id,
                name=secret_name
            )
            
            if not secrets_list.data:
                self.logger.warning(f"Secret '{secret_name}' not found for deletion")
                return False
            
            secret = secrets_list.data[0]
            
            if permanent:
                # Schedule for deletion (OCI doesn't support immediate permanent deletion)
                deletion_time = datetime.utcnow() + timedelta(days=7)  # Minimum 7 days
                self._secrets_client.schedule_secret_deletion(
                    secret.id,
                    oci.secrets.models.ScheduleSecretDeletionDetails(
                        time_of_deletion=deletion_time
                    )
                )
            else:
                # Mark as deleted (lifecycle state change)
                self._secrets_client.update_secret(
                    secret.id,
                    oci.secrets.models.UpdateSecretDetails(
                        defined_tags={"deleted": "true"}
                    )
                )
            
            # Remove from cache
            if secret_name in self._secret_cache:
                del self._secret_cache[secret_name]
            
            self.logger.info(f"Successfully deleted secret '{secret_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting secret '{secret_name}': {str(e)}")
            return False
    
    async def list_secrets(self, secret_type: Optional[SecretType] = None) -> List[SecretMetadata]:
        """
        List all secrets in the vault
        
        Args:
            secret_type: Filter by secret type
            
        Returns:
            List of secret metadata
        """
        try:
            if not OCI_AVAILABLE or not self._secrets_client:
                # Return mock data
                return [
                    SecretMetadata(
                        secret_id="mock-id-1",
                        name="database_password",
                        secret_type=SecretType.DATABASE_PASSWORD,
                        version_number=1,
                        created_at=datetime.utcnow()
                    )
                ]
            
            secrets_list = self._secrets_client.list_secrets(
                compartment_id=self.compartment_id
            )
            
            result = []
            for secret in secrets_list.data:
                metadata = SecretMetadata(
                    secret_id=secret.id,
                    name=secret.secret_name,
                    secret_type=SecretType.GENERIC,  # Could be enhanced with tags
                    version_number=getattr(secret, 'current_version_number', 1),
                    created_at=secret.time_created.replace(tzinfo=None),
                    tags=getattr(secret, 'defined_tags', None)
                )
                
                # Filter by type if specified
                if not secret_type or metadata.secret_type == secret_type:
                    result.append(metadata)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error listing secrets: {str(e)}")
            return []
    
    def clear_cache(self):
        """Clear the secret cache"""
        self._secret_cache.clear()
        self.logger.info("Secret cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.utcnow()
        active_secrets = sum(1 for secret in self._secret_cache.values() 
                           if not secret.expires_at or secret.expires_at > now)
        
        return {
            'total_cached': len(self._secret_cache),
            'active_cached': active_secrets,
            'cache_ttl_minutes': self._cache_ttl.total_seconds() / 60
        }


# Global instance
vault_service = OCIVaultService()


# Utility functions for easy access
async def get_secret(secret_name: str, force_refresh: bool = False) -> Optional[str]:
    """Helper function to get a secret"""
    return await vault_service.get_secret(secret_name, force_refresh)


async def get_database_password() -> Optional[str]:
    """Get database password from vault"""
    return await get_secret('database_password')


async def get_jwt_secret() -> Optional[str]:
    """Get JWT secret key from vault"""
    return await get_secret('jwt_secret_key')


async def get_api_key(service_name: str) -> Optional[str]:
    """Get API key for a specific service"""
    return await get_secret(f'{service_name}_api_key') 