"""
Unit tests for OCI Vault Service
Tests secret management, caching, and OCI integration
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import base64

from app.services.oci_vault_service import (
    OCIVaultService, 
    SecretType, 
    SecretMetadata, 
    SecretValue,
    vault_service,
    get_secret,
    get_database_password,
    get_jwt_secret,
    get_api_key
)


@pytest.mark.unit
class TestOCIVaultService:
    """Test suite for OCI Vault Service functionality."""
    
    def test_vault_service_initialization_oci_available(self):
        """Test vault service initialization when OCI SDK is available."""
        with patch('app.services.oci_vault_service.OCI_AVAILABLE', True), \
             patch('app.services.oci_vault_service.settings') as mock_settings:
            
            mock_settings.OCI_COMPARTMENT_ID = "test-compartment"
            mock_settings.OCI_VAULT_ID = "test-vault"
            mock_settings.OCI_KMS_KEY_ID = "test-key"
            
            with patch.object(OCIVaultService, '_initialize_clients') as mock_init:
                vault = OCIVaultService()
                
                assert vault.compartment_id == "test-compartment"
                assert vault.vault_id == "test-vault"
                assert vault.kms_key_id == "test-key"
                mock_init.assert_called_once()
    
    def test_vault_service_initialization_oci_unavailable(self):
        """Test vault service initialization when OCI SDK is unavailable."""
        with patch('app.services.oci_vault_service.OCI_AVAILABLE', False):
            vault = OCIVaultService()
            
            assert vault._vault_client is None
            assert vault._secrets_client is None
    
    @pytest.mark.asyncio
    async def test_get_secret_from_cache(self):
        """Test getting secret from cache when available and valid."""
        vault = OCIVaultService()
        
        # Setup cache with valid secret
        secret_metadata = SecretMetadata(
            secret_id="test-id",
            name="test-secret",
            secret_type=SecretType.GENERIC,
            version_number=1,
            created_at=datetime.utcnow()
        )
        
        cached_secret = SecretValue(
            value="cached-secret-value",
            metadata=secret_metadata,
            retrieved_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=10)  # Valid for 10 more minutes
        )
        
        vault._secret_cache["test-secret"] = cached_secret
        
        result = await vault.get_secret("test-secret")
        
        assert result == "cached-secret-value"
    
    @pytest.mark.asyncio
    async def test_get_secret_cache_expired(self):
        """Test getting secret when cache entry is expired."""
        vault = OCIVaultService()
        
        # Setup cache with expired secret
        secret_metadata = SecretMetadata(
            secret_id="test-id",
            name="test-secret",
            secret_type=SecretType.GENERIC,
            version_number=1,
            created_at=datetime.utcnow()
        )
        
        expired_secret = SecretValue(
            value="expired-secret-value",
            metadata=secret_metadata,
            retrieved_at=datetime.utcnow() - timedelta(hours=1),
            expires_at=datetime.utcnow() - timedelta(minutes=10)  # Expired 10 minutes ago
        )
        
        vault._secret_cache["test-secret"] = expired_secret
        
        with patch.object(vault, '_retrieve_from_vault', return_value=None) as mock_retrieve:
            result = await vault.get_secret("test-secret")
            
            # Should attempt to retrieve from vault since cache is expired
            mock_retrieve.assert_called_once_with("test-secret")
            assert "test-secret" not in vault._secret_cache  # Expired entry removed
    
    @pytest.mark.asyncio
    async def test_get_secret_mock_implementation(self):
        """Test getting secret using mock implementation when OCI unavailable."""
        vault = OCIVaultService()
        
        # Simulate OCI unavailable
        vault._secrets_client = None
        
        result = await vault.get_secret("database_password")
        
        assert result == "mock_db_password_123"
    
    @pytest.mark.asyncio
    async def test_get_secret_force_refresh(self):
        """Test getting secret with force refresh bypassing cache."""
        vault = OCIVaultService()
        
        # Setup cache
        secret_metadata = SecretMetadata(
            secret_id="test-id",
            name="test-secret",
            secret_type=SecretType.GENERIC,
            version_number=1,
            created_at=datetime.utcnow()
        )
        
        cached_secret = SecretValue(
            value="cached-value",
            metadata=secret_metadata,
            retrieved_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        
        vault._secret_cache["test-secret"] = cached_secret
        
        with patch.object(vault, '_retrieve_from_vault', return_value=None) as mock_retrieve:
            await vault.get_secret("test-secret", force_refresh=True)
            
            # Should bypass cache and call vault
            mock_retrieve.assert_called_once_with("test-secret")
    
    @pytest.mark.asyncio
    async def test_retrieve_from_vault_success(self):
        """Test successful secret retrieval from OCI Vault."""
        vault = OCIVaultService()
        vault.compartment_id = "test-compartment"
        
        # Mock OCI clients
        mock_secrets_client = Mock()
        vault._secrets_client = mock_secrets_client
        
        # Mock list_secrets response
        mock_secret = Mock()
        mock_secret.id = "ocid1.secret.test"
        mock_secret.time_created = datetime.utcnow()
        mock_secret.defined_tags = {"environment": "test"}
        
        mock_list_response = Mock()
        mock_list_response.data = [mock_secret]
        mock_secrets_client.list_secrets.return_value = mock_list_response
        
        # Mock get_secret_bundle response
        secret_content = base64.b64encode(b"test-secret-value").decode('utf-8')
        mock_bundle_content = Mock()
        mock_bundle_content.content = secret_content
        
        mock_bundle_data = Mock()
        mock_bundle_data.secret_bundle_content = mock_bundle_content
        mock_bundle_data.version_number = 1
        
        mock_bundle_response = Mock()
        mock_bundle_response.data = mock_bundle_data
        mock_secrets_client.get_secret_bundle.return_value = mock_bundle_response
        
        result = await vault._retrieve_from_vault("test-secret")
        
        assert result is not None
        assert result.value == "test-secret-value"
        assert result.metadata.secret_id == "ocid1.secret.test"
        assert result.metadata.version_number == 1
    
    @pytest.mark.asyncio
    async def test_retrieve_from_vault_not_found(self):
        """Test secret retrieval when secret is not found in vault."""
        vault = OCIVaultService()
        vault.compartment_id = "test-compartment"
        
        # Mock OCI clients
        mock_secrets_client = Mock()
        vault._secrets_client = mock_secrets_client
        
        # Mock empty response
        mock_list_response = Mock()
        mock_list_response.data = []
        mock_secrets_client.list_secrets.return_value = mock_list_response
        
        result = await vault._retrieve_from_vault("nonexistent-secret")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_store_secret_success(self):
        """Test successful secret storage in OCI Vault."""
        vault = OCIVaultService()
        vault.compartment_id = "test-compartment"
        vault.vault_id = "test-vault"
        vault.kms_key_id = "test-key"
        
        # Mock OCI clients
        mock_secrets_client = Mock()
        vault._secrets_client = mock_secrets_client
        
        mock_response = Mock()
        mock_secrets_client.create_secret.return_value = mock_response
        
        result = await vault.store_secret(
            secret_name="test-secret",
            secret_value="test-value",
            secret_type=SecretType.API_KEY,
            description="Test secret",
            tags={"environment": "test"}
        )
        
        assert result is True
        mock_secrets_client.create_secret.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_secret_oci_unavailable(self):
        """Test secret storage when OCI is unavailable."""
        vault = OCIVaultService()
        vault._secrets_client = None
        
        result = await vault.store_secret(
            secret_name="test-secret",
            secret_value="test-value"
        )
        
        assert result is True  # Mock implementation returns True
    
    @pytest.mark.asyncio
    async def test_rotate_secret_success(self):
        """Test successful secret rotation."""
        vault = OCIVaultService()
        vault.compartment_id = "test-compartment"
        
        # Mock OCI clients
        mock_secrets_client = Mock()
        vault._secrets_client = mock_secrets_client
        
        # Mock list_secrets response
        mock_secret = Mock()
        mock_secret.id = "ocid1.secret.test"
        
        mock_list_response = Mock()
        mock_list_response.data = [mock_secret]
        mock_secrets_client.list_secrets.return_value = mock_list_response
        
        # Mock update_secret
        mock_secrets_client.update_secret.return_value = Mock()
        
        result = await vault.rotate_secret("test-secret", "new-value")
        
        assert result is True
        mock_secrets_client.update_secret.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rotate_secret_not_found(self):
        """Test secret rotation when secret is not found."""
        vault = OCIVaultService()
        vault.compartment_id = "test-compartment"
        
        # Mock OCI clients
        mock_secrets_client = Mock()
        vault._secrets_client = mock_secrets_client
        
        # Mock empty response
        mock_list_response = Mock()
        mock_list_response.data = []
        mock_secrets_client.list_secrets.return_value = mock_list_response
        
        result = await vault.rotate_secret("nonexistent-secret", "new-value")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_secret_success(self):
        """Test successful secret deletion."""
        vault = OCIVaultService()
        vault.compartment_id = "test-compartment"
        
        # Mock OCI clients
        mock_secrets_client = Mock()
        vault._secrets_client = mock_secrets_client
        
        # Mock list_secrets response
        mock_secret = Mock()
        mock_secret.id = "ocid1.secret.test"
        
        mock_list_response = Mock()
        mock_list_response.data = [mock_secret]
        mock_secrets_client.list_secrets.return_value = mock_list_response
        
        # Mock update_secret (for soft delete)
        mock_secrets_client.update_secret.return_value = Mock()
        
        result = await vault.delete_secret("test-secret", permanent=False)
        
        assert result is True
        mock_secrets_client.update_secret.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_secret_permanent(self):
        """Test permanent secret deletion."""
        vault = OCIVaultService()
        vault.compartment_id = "test-compartment"
        
        # Mock OCI clients
        mock_secrets_client = Mock()
        vault._secrets_client = mock_secrets_client
        
        # Mock list_secrets response
        mock_secret = Mock()
        mock_secret.id = "ocid1.secret.test"
        
        mock_list_response = Mock()
        mock_list_response.data = [mock_secret]
        mock_secrets_client.list_secrets.return_value = mock_list_response
        
        # Mock schedule_secret_deletion
        mock_secrets_client.schedule_secret_deletion.return_value = Mock()
        
        result = await vault.delete_secret("test-secret", permanent=True)
        
        assert result is True
        mock_secrets_client.schedule_secret_deletion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_secrets_success(self):
        """Test successful listing of secrets."""
        vault = OCIVaultService()
        vault.compartment_id = "test-compartment"
        
        # Mock OCI clients
        mock_secrets_client = Mock()
        vault._secrets_client = mock_secrets_client
        
        # Mock list_secrets response
        mock_secret1 = Mock()
        mock_secret1.id = "ocid1.secret1.test"
        mock_secret1.secret_name = "secret1"
        mock_secret1.time_created = datetime.utcnow()
        mock_secret1.current_version_number = 1
        mock_secret1.defined_tags = {}
        
        mock_secret2 = Mock()
        mock_secret2.id = "ocid1.secret2.test"
        mock_secret2.secret_name = "secret2"
        mock_secret2.time_created = datetime.utcnow()
        mock_secret2.current_version_number = 2
        mock_secret2.defined_tags = {"type": "api_key"}
        
        mock_list_response = Mock()
        mock_list_response.data = [mock_secret1, mock_secret2]
        mock_secrets_client.list_secrets.return_value = mock_list_response
        
        result = await vault.list_secrets()
        
        assert len(result) == 2
        assert result[0].name == "secret1"
        assert result[1].name == "secret2"
        assert result[1].version_number == 2
    
    @pytest.mark.asyncio
    async def test_list_secrets_mock_implementation(self):
        """Test listing secrets using mock implementation."""
        vault = OCIVaultService()
        vault._secrets_client = None
        
        result = await vault.list_secrets()
        
        assert len(result) == 1
        assert result[0].name == "database_password"
        assert result[0].secret_type == SecretType.DATABASE_PASSWORD
    
    def test_cache_secret(self):
        """Test secret caching functionality."""
        vault = OCIVaultService()
        
        secret_metadata = SecretMetadata(
            secret_id="test-id",
            name="test-secret",
            secret_type=SecretType.GENERIC,
            version_number=1,
            created_at=datetime.utcnow()
        )
        
        secret_value = SecretValue(
            value="test-value",
            metadata=secret_metadata,
            retrieved_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        
        vault._cache_secret("test-secret", secret_value)
        
        assert "test-secret" in vault._secret_cache
        assert vault._secret_cache["test-secret"].value == "test-value"
    
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        vault = OCIVaultService()
        
        # Add something to cache
        vault._secret_cache["test"] = "value"
        
        assert len(vault._secret_cache) == 1
        
        vault.clear_cache()
        
        assert len(vault._secret_cache) == 0
    
    def test_get_cache_stats(self):
        """Test cache statistics functionality."""
        vault = OCIVaultService()
        
        # Add active and expired secrets
        active_secret = SecretValue(
            value="active",
            metadata=Mock(),
            retrieved_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        
        expired_secret = SecretValue(
            value="expired",
            metadata=Mock(),
            retrieved_at=datetime.utcnow(),
            expires_at=datetime.utcnow() - timedelta(minutes=10)
        )
        
        vault._secret_cache["active"] = active_secret
        vault._secret_cache["expired"] = expired_secret
        
        stats = vault.get_cache_stats()
        
        assert stats["total_cached"] == 2
        assert stats["active_cached"] == 1
        assert stats["cache_ttl_minutes"] == 15.0


@pytest.mark.unit
class TestOCIVaultServiceUtilityFunctions:
    """Test suite for utility functions."""
    
    @pytest.mark.asyncio
    async def test_get_secret_function(self):
        """Test the standalone get_secret function."""
        with patch('app.services.oci_vault_service.vault_service') as mock_vault:
            mock_vault.get_secret = AsyncMock(return_value="test-value")
            
            result = await get_secret("test-secret")
            
            assert result == "test-value"
            mock_vault.get_secret.assert_called_once_with("test-secret", False)
    
    @pytest.mark.asyncio
    async def test_get_database_password_function(self):
        """Test the get_database_password utility function."""
        with patch('app.services.oci_vault_service.get_secret') as mock_get_secret:
            mock_get_secret.return_value = "db-password"
            
            result = await get_database_password()
            
            assert result == "db-password"
            mock_get_secret.assert_called_once_with('database_password')
    
    @pytest.mark.asyncio
    async def test_get_jwt_secret_function(self):
        """Test the get_jwt_secret utility function."""
        with patch('app.services.oci_vault_service.get_secret') as mock_get_secret:
            mock_get_secret.return_value = "jwt-secret"
            
            result = await get_jwt_secret()
            
            assert result == "jwt-secret"
            mock_get_secret.assert_called_once_with('jwt_secret_key')
    
    @pytest.mark.asyncio
    async def test_get_api_key_function(self):
        """Test the get_api_key utility function."""
        with patch('app.services.oci_vault_service.get_secret') as mock_get_secret:
            mock_get_secret.return_value = "api-key"
            
            result = await get_api_key("groq")
            
            assert result == "api-key"
            mock_get_secret.assert_called_once_with('groq_api_key')


@pytest.mark.unit
class TestOCIVaultServiceErrorHandling:
    """Test suite for error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_get_secret_exception_handling(self):
        """Test exception handling in get_secret."""
        vault = OCIVaultService()
        
        with patch.object(vault, '_retrieve_from_vault', side_effect=Exception("Test error")):
            result = await vault.get_secret("test-secret")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_store_secret_exception_handling(self):
        """Test exception handling in store_secret."""
        vault = OCIVaultService()
        
        # Mock OCI client that raises exception
        mock_secrets_client = Mock()
        mock_secrets_client.create_secret.side_effect = Exception("Test error")
        vault._secrets_client = mock_secrets_client
        vault.compartment_id = "test"
        vault.vault_id = "test"
        vault.kms_key_id = "test"
        
        result = await vault.store_secret("test-secret", "test-value")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_secret_type_enum_validation(self):
        """Test SecretType enum validation."""
        # Test all valid secret types
        valid_types = [
            SecretType.DATABASE_PASSWORD,
            SecretType.API_KEY,
            SecretType.JWT_SECRET,
            SecretType.ENCRYPTION_KEY,
            SecretType.CERTIFICATE,
            SecretType.PRIVATE_KEY,
            SecretType.GENERIC
        ]
        
        for secret_type in valid_types:
            assert isinstance(secret_type.value, str)
            assert len(secret_type.value) > 0 