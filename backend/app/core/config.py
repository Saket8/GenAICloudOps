from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "GenAI CloudOps API"
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:3001",  # Alternative React port
        "http://localhost:8080",  # Alternative dev port
    ]
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./genai_cloudops.db"
    
    # Security Settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Redis Settings
    REDIS_ENABLED: bool = False  # Disabled by default; enable when a Redis instance is available
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    # Security Settings
    SECURITY_MIDDLEWARE_ENABLED: bool = False  # Temporarily disabled to fix login timeout
    RATE_LIMITING_ENABLED: bool = False  # Temporarily disabled
    INPUT_VALIDATION_ENABLED: bool = True
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Performance Settings
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    QUERY_TIMEOUT: int = 30
    
    # Compression Settings
    COMPRESSION_ENABLED: bool = True
    COMPRESSION_LEVEL: int = 6
    COMPRESSION_MIN_SIZE: int = 1024  # 1KB
    
    # OCI Configuration  
    OCI_CONFIG_FILE: str = os.path.expanduser("~/.oci/config")
    OCI_PROFILE: str = "DEFAULT"
    OCI_REGION: str = "eu-frankfurt-1"
    OCI_TENANCY_ID: str = ""
    OCI_USER_ID: str = ""
    OCI_FINGERPRINT: str = ""
    OCI_KEY_FILE: str = ""
    
    # Global Dummy Mode Flags (disable all live external connections by default)
    USE_DUMMY_OCI: bool = True
    USE_DUMMY_KUBERNETES: bool = True
    USE_DUMMY_VAULT: bool = True
    
    # OCI Vault Configuration
    OCI_VAULT_ENABLED: bool = True
    OCI_COMPARTMENT_ID: str = ""  # Required for vault operations
    OCI_VAULT_ID: str = ""  # Vault OCID for storing secrets
    OCI_KMS_KEY_ID: str = ""  # KMS key OCID for encryption
    OCI_USE_INSTANCE_PRINCIPAL: bool = False  # Use instance principal authentication in OKE
    
    # Vault Cache Configuration
    VAULT_CACHE_TTL_MINUTES: int = 15  # Cache TTL for secrets
    VAULT_ENABLE_CACHING: bool = True  # Enable secret caching
    VAULT_MAX_CACHE_SIZE: int = 1000  # Maximum number of cached secrets
    
    # Monitoring Configuration
    MONITORING_CACHE_TTL: int = 300  # 5 minutes cache for monitoring data
    ALERT_HISTORY_HOURS: int = 24  # Default hours of alert history to retrieve
    MAX_LOG_SEARCH_RESULTS: int = 1000  # Maximum log search results per query
    HEALTH_SCORE_THRESHOLD_HEALTHY: float = 90.0
    HEALTH_SCORE_THRESHOLD_WARNING: float = 70.0
    HEALTH_SCORE_THRESHOLD_DEGRADED: float = 50.0
    
    # GenAI Configuration
    GROQ_API_KEY: str = "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"
    GROQ_MODEL: str = "llama3-8b-8192"  # Default Groq model
    GROQ_MAX_TOKENS: int = 1024
    GROQ_TEMPERATURE: float = 0.7
    GROQ_TIMEOUT: int = 30  # seconds
    GENAI_CACHE_TTL: int = 3600  # 1 hour cache for GenAI responses
    GENAI_RATE_LIMIT_PER_MINUTE: int = 100
    GENAI_MAX_CONTEXT_LENGTH: int = 4000
    GENAI_ENABLE_CACHING: bool = False  # Disabled for now - can enable with Redis later
    GENAI_ENABLE_BATCHING: bool = True
    GENAI_BATCH_SIZE: int = 5
    GENAI_FALLBACK_MODEL: str = "mixtral-8x7b-32768"
    # Added for GenAIService compatibility
    GENAI_PRIMARY_MODEL: str = "llama3-8b-8192"
    GENAI_MAX_RETRIES: int = 2
    GENAI_TIMEOUT: int = 30
    
    # Optional Enhancement Features
    
    # Prometheus Metrics
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_URL: str = "http://localhost:9090"
    
    # Grafana Integration
    GRAFANA_ENABLED: bool = False
    GRAFANA_URL: str = "http://localhost:3000"
    GRAFANA_API_KEY: str = ""
    GRAFANA_USERNAME: str = "admin"
    GRAFANA_PASSWORD: str = "admin"
    
    # Notification Service
    NOTIFICATIONS_ENABLED: bool = True
    
    # Email Notifications
    EMAIL_ENABLED: bool = False
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SENDER_EMAIL: str = "noreply@genai-cloudops.com"
    SENDER_NAME: str = "GenAI CloudOps Dashboard"
    ADMIN_EMAIL: str = "admin@genai-cloudops.com"
    DEVOPS_EMAIL: str = "devops@genai-cloudops.com"
    BUSINESS_EMAIL: str = "business@genai-cloudops.com"
    
    # Slack Notifications
    SLACK_ENABLED: bool = False
    SLACK_BOT_TOKEN: str = ""
    SLACK_WEBHOOK_URL: str = ""
    SLACK_DEFAULT_CHANNEL: str = "#alerts"
    ADMIN_SLACK_ID: str = ""
    
    # Auto-Remediation
    AUTO_REMEDIATION_ENABLED: bool = False
    AUTO_APPROVAL_ENABLED: bool = False
    MAX_CONCURRENT_REMEDIATIONS: int = 3
    REMEDIATION_DRY_RUN: bool = True
    
    # Dashboard URL for notifications
    DASHBOARD_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 