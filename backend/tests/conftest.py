"""
Pytest configuration and fixtures for GenAI CloudOps testing
Provides shared fixtures for database, authentication, mocking, and test utilities
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from fastapi import FastAPI
import tempfile
import shutil

# Import app components
from app.main import app
from app.core.config import settings
from app.core.database import get_db, Base
from app.models.user import User, Role, UserRole, RoleEnum
from app.services.auth_service import AuthService
from app.core.security import get_password_hash, create_access_token


# Test Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def override_get_db(db_session: Session):
    """Override the get_db dependency with test database."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    return _override_get_db


@pytest.fixture(scope="function")
def client(override_get_db) -> TestClient:
    """Create a test client with overridden dependencies."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_admin_user(db_session: Session) -> User:
    """Create a test admin user."""
    # Create admin role
    admin_role = Role(
        name=RoleEnum.ADMIN,
        description="Administrator role",
        permissions=["admin", "read", "write", "execute"]
    )
    db_session.add(admin_role)
    db_session.flush()
    
    # Create admin user
    admin_user = User(
        username="admin_test",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Test Admin",
        is_active=True
    )
    db_session.add(admin_user)
    db_session.flush()
    
    # Assign admin role
    user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
    db_session.add(user_role)
    db_session.commit()
    
    return admin_user


@pytest.fixture(scope="function")
def test_regular_user(db_session: Session) -> User:
    """Create a test regular user."""
    # Create user role
    user_role = Role(
        name=RoleEnum.USER,
        description="Regular user role",
        permissions=["read"]
    )
    db_session.add(user_role)
    db_session.flush()
    
    # Create regular user
    regular_user = User(
        username="user_test",
        email="user@test.com",
        hashed_password=get_password_hash("user123"),
        full_name="Test User",
        is_active=True
    )
    db_session.add(regular_user)
    db_session.flush()
    
    # Assign user role
    user_role_assignment = UserRole(user_id=regular_user.id, role_id=user_role.id)
    db_session.add(user_role_assignment)
    db_session.commit()
    
    return regular_user


@pytest.fixture(scope="function")
def admin_token(test_admin_user: User) -> str:
    """Create an admin access token."""
    return create_access_token(data={"sub": test_admin_user.username})


@pytest.fixture(scope="function")
def user_token(test_regular_user: User) -> str:
    """Create a regular user access token."""
    return create_access_token(data={"sub": test_regular_user.username})


@pytest.fixture(scope="function")
def admin_headers(admin_token: str) -> dict:
    """Create admin authorization headers."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def user_headers(user_token: str) -> dict:
    """Create user authorization headers."""
    return {"Authorization": f"Bearer {user_token}"}


# Mock OCI SDK fixtures
@pytest.fixture(scope="function")
def mock_oci_config():
    """Mock OCI configuration."""
    return {
        "user": "ocid1.user.oc1..test",
        "key_file": "/test/key.pem",
        "fingerprint": "test:fingerprint",
        "tenancy": "ocid1.tenancy.oc1..test",
        "region": "us-ashburn-1"
    }


@pytest.fixture(scope="function")
def mock_oci_vault_client():
    """Mock OCI Vault client."""
    with patch('app.services.oci_vault_service.VaultsClient') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_oci_secrets_client():
    """Mock OCI Secrets client."""
    with patch('app.services.oci_vault_service.SecretsClient') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_oci_compute_client():
    """Mock OCI Compute client."""
    with patch('app.services.cloud_service.ComputeClient') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_kubernetes_client():
    """Mock Kubernetes client."""
    with patch('kubernetes.client.CoreV1Api') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_groq_client():
    """Mock Groq API client."""
    with patch('groq.Groq') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


# Test data fixtures
@pytest.fixture(scope="function")
def sample_oci_instance():
    """Sample OCI instance data."""
    return {
        "id": "ocid1.instance.oc1.test",
        "display_name": "test-instance",
        "lifecycle_state": "RUNNING",
        "availability_domain": "test-AD-1",
        "compartment_id": "ocid1.compartment.oc1.test",
        "shape": "VM.Standard2.1",
        "time_created": "2024-01-01T00:00:00Z"
    }


@pytest.fixture(scope="function")
def sample_kubernetes_pod():
    """Sample Kubernetes pod data."""
    return {
        "metadata": {
            "name": "test-pod",
            "namespace": "default",
            "labels": {"app": "test"}
        },
        "status": {
            "phase": "Running",
            "pod_ip": "10.0.0.1"
        },
        "spec": {
            "containers": [
                {
                    "name": "test-container",
                    "image": "nginx:latest"
                }
            ]
        }
    }


@pytest.fixture(scope="function")
def sample_genai_response():
    """Sample GenAI API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "This is a test GenAI response.",
                    "role": "assistant"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "total_tokens": 18
        }
    }


# Environment and configuration fixtures
@pytest.fixture(scope="function", autouse=True)
def test_environment():
    """Set up test environment variables."""
    test_vars = {
        "ENVIRONMENT": "test",
        "DATABASE_URL": SQLALCHEMY_DATABASE_URL,
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "OCI_VAULT_ENABLED": "false",  # Disable vault for most tests
        "GROQ_API_KEY": "test-groq-key",
        "REDIS_URL": "redis://localhost:6379/1"
    }
    
    # Store original values
    original_values = {}
    for key, value in test_vars.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original values
    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture(scope="function")
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


# Async fixtures
@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator:
    """Create an async test client."""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Mock service fixtures
@pytest.fixture(scope="function")
def mock_monitoring_service():
    """Mock monitoring service."""
    with patch('app.services.monitoring_service.MonitoringService') as mock_service:
        mock_instance = Mock()
        mock_service.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_remediation_service():
    """Mock remediation service."""
    with patch('app.services.remediation_service.RemediationService') as mock_service:
        mock_instance = Mock()
        mock_service.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_chatbot_service():
    """Mock chatbot service."""
    with patch('app.services.chatbot_service.ChatbotService') as mock_service:
        mock_instance = Mock()
        mock_service.return_value = mock_instance
        yield mock_instance


# Performance testing fixtures
@pytest.fixture(scope="function")
def performance_timer():
    """Timer fixture for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Utility functions for tests
def assert_status_code(response, expected_status: int):
    """Assert response status code with detailed error message."""
    if response.status_code != expected_status:
        error_detail = ""
        try:
            error_detail = f" - Response: {response.json()}"
        except:
            error_detail = f" - Raw response: {response.text}"
        
        pytest.fail(
            f"Expected status {expected_status}, got {response.status_code}{error_detail}"
        )


def assert_response_schema(response_data: dict, required_fields: list):
    """Assert that response contains all required fields."""
    missing_fields = [field for field in required_fields if field not in response_data]
    if missing_fields:
        pytest.fail(f"Response missing required fields: {missing_fields}")


# Database utilities
def create_test_data(db_session: Session, model_class, **kwargs):
    """Helper to create test data."""
    instance = model_class(**kwargs)
    db_session.add(instance)
    db_session.commit()
    db_session.refresh(instance)
    return instance


# Mock external API responses
@pytest.fixture(scope="function")
def mock_successful_oci_response():
    """Mock successful OCI API response."""
    return Mock(
        status=200,
        data=Mock(
            resources=[
                Mock(
                    id="ocid1.resource.oc1.test",
                    display_name="test-resource",
                    lifecycle_state="ACTIVE"
                )
            ]
        )
    )


@pytest.fixture(scope="function")
def mock_error_oci_response():
    """Mock error OCI API response."""
    from oci.exceptions import ServiceError
    return ServiceError(
        status=404,
        code="NotFound",
        headers={},
        message="Resource not found"
    ) 