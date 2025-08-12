import asyncio
import oci
import json
import logging
import os
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    # Create dummy decorators when tenacity is not available
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    stop_after_attempt = wait_exponential = retry_if_exception_type = lambda *args, **kwargs: None

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import os
from app.core.exceptions import ExternalServiceError, NotFoundError

logger = logging.getLogger(__name__)

# Configuration and data classes
@dataclass
class OCIMetrics:
    """Data class for OCI resource metrics"""
    cpu_utilization: float
    memory_utilization: float
    network_bytes_in: int
    network_bytes_out: int
    timestamp: datetime

@dataclass 
class OCIResource:
    """Data class for OCI resource information"""
    id: str
    name: str
    state: str
    resource_type: str
    compartment_id: str
    availability_domain: Optional[str] = None
    shape: Optional[str] = None
    metrics: Optional[OCIMetrics] = None

class ResourceType(Enum):
    """Enumeration of supported OCI resource types"""
    COMPUTE_INSTANCE = "compute_instance"
    DATABASE = "database"
    OKE_CLUSTER = "oke_cluster"
    API_GATEWAY = "api_gateway"
    LOAD_BALANCER = "load_balancer"
    AUTONOMOUS_DATABASE = "autonomous_database"

class OCIAuthConfig:
    """OCI authentication configuration management"""
    
    def __init__(self):
        from app.core.config import settings
        
        self.config_file = os.getenv("OCI_CONFIG_FILE", settings.OCI_CONFIG_FILE)
        self.profile = os.getenv("OCI_PROFILE", settings.OCI_PROFILE)
        self.region = os.getenv("OCI_REGION", settings.OCI_REGION)
        
        # Environment variable based auth (for containerized environments)
        self.tenancy_id = os.getenv("OCI_TENANCY_ID", settings.OCI_TENANCY_ID)
        self.user_id = os.getenv("OCI_USER_ID", settings.OCI_USER_ID)
        self.fingerprint = os.getenv("OCI_FINGERPRINT", settings.OCI_FINGERPRINT)
        self.key_file = os.getenv("OCI_KEY_FILE", settings.OCI_KEY_FILE)
        
    def get_config(self) -> Dict[str, str]:
        """Get OCI configuration for SDK initialization"""
        if self.tenancy_id and self.user_id and self.fingerprint and self.key_file:
            # Use environment variables
            logger.info("Using OCI configuration from environment variables")
            return {
                "user": self.user_id,
                "key_file": self.key_file,
                "fingerprint": self.fingerprint,
                "tenancy": self.tenancy_id,
                "region": self.region
            }
        else:
            # Use config file
            try:
                # Expand Windows paths properly
                expanded_config_file = os.path.expanduser(self.config_file)
                if not os.path.exists(expanded_config_file):
                    # Try the literal path on Windows
                    if os.path.exists(self.config_file):
                        expanded_config_file = self.config_file
                    else:
                        raise FileNotFoundError(f"OCI config file not found at {self.config_file} or {expanded_config_file}")
                
                logger.info(f"Loading OCI config from: {expanded_config_file}")
                config = oci.config.from_file(expanded_config_file, self.profile)
                
                # Validate config has required fields
                required_fields = ["user", "tenancy", "region", "fingerprint"]
                missing_fields = [field for field in required_fields if not config.get(field)]
                if missing_fields:
                    raise ValueError(f"OCI config missing required fields: {missing_fields}")
                
                logger.info(f"✅ OCI config loaded successfully for region: {config.get('region')}")
                return config
                
            except Exception as e:
                logger.error(f"❌ Failed to load OCI config file: {e}")
                logger.error(f"Config file path: {self.config_file}")
                logger.error(f"Profile: {self.profile}")
                # Don't fall back to mock - raise the error so we know what's wrong
                raise RuntimeError(f"OCI configuration failed: {e}")

class OCICacheManager:
    """Redis-based caching for OCI API responses"""
    
    def __init__(self):
        # Check if Redis is explicitly disabled
        from app.core.config import settings
        if not settings.REDIS_ENABLED:
            logger.info("Redis caching disabled via configuration")
            self.cache_enabled = False
            return
            
        if not REDIS_AVAILABLE:
            logger.warning("Redis module not available - caching disabled")
            self.cache_enabled = False
            return
            
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            self.cache_enabled = True
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis cache unavailable: {e}")
            self.cache_enabled = False
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached data"""
        if not self.cache_enabled:
            return None
        try:
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, data: Dict, ttl: int = 300) -> bool:
        """Set cached data with TTL (default 5 minutes)"""
        if not self.cache_enabled:
            return False
        try:
            self.redis_client.setex(key, ttl, json.dumps(data, default=str))
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cached data"""
        if not self.cache_enabled:
            return False
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False

class OCIService:
    """Comprehensive OCI SDK integration service"""
    
    def __init__(self):
        from app.core.config import settings
        self.auth_config = OCIAuthConfig()
        self.cache = OCICacheManager()
        self.clients = {}
        self.oci_available = False
        self.config = None
        # If dummy mode is enabled, keep OCI unavailable and skip client init
        if getattr(settings, 'USE_DUMMY_OCI', False):
            logger.info("USE_DUMMY_OCI is True - skipping OCI client initialization and using mock data")
            self.oci_available = False
            self.clients = {}
            self.config = {"region": settings.OCI_REGION}
        else:
            self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize OCI SDK clients"""
        try:
            # Get OCI configuration
            self.config = self.auth_config.get_config()
            
            # Validate configuration first
            oci.config.validate_config(self.config)
            logger.info(f"✅ OCI config validation passed for tenancy: {self.config.get('tenancy', 'unknown')}")
            
            # Core clients
            self.clients['compute'] = oci.core.ComputeClient(self.config)
            self.clients['identity'] = oci.identity.IdentityClient(self.config)
            self.clients['monitoring'] = oci.monitoring.MonitoringClient(self.config)
            
            # Logging client for alerts and logs
            self.clients['logging'] = oci.logging.LoggingManagementClient(self.config)
            self.clients['log_search'] = oci.loggingsearch.LogSearchClient(self.config)
            
            # Database clients
            self.clients['database'] = oci.database.DatabaseClient(self.config)
            
            # Container and networking clients
            self.clients['container_engine'] = oci.container_engine.ContainerEngineClient(self.config)
            self.clients['load_balancer'] = oci.load_balancer.LoadBalancerClient(self.config)
            self.clients['network_load_balancer'] = oci.network_load_balancer.NetworkLoadBalancerClient(self.config)

            
            # Virtual network client
            self.clients['virtual_network'] = oci.core.VirtualNetworkClient(self.config)
            
            # Storage clients - CRITICAL: These were missing!
            self.clients['block_storage'] = oci.core.BlockstorageClient(self.config)
            self.clients['file_storage'] = oci.file_storage.FileStorageClient(self.config)
            
            logger.info("✅ OCI SDK clients initialized successfully")
            
            # Mark as potentially available - actual connection test will be done on-demand
            self.oci_available = True
            logger.info("🔄 OCI clients created, connection will be tested on first API call")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize OCI clients: {e}")
            if self.config:
                logger.error(f"Config details: region={self.config.get('region')}, user={self.config.get('user', 'unknown')}")
            logger.warning("🔄 Falling back to mock data for development")
            self.oci_available = False
            self.clients = {}
            self.config = {"region": "us-ashburn-1"}

    async def test_connection(self) -> bool:
        """Test OCI connection asynchronously on-demand"""
        if not self.oci_available or not self.clients.get('identity'):
            return False
            
        try:
            # Test the connection with a simple call using asyncio
            identity_client = self.clients['identity']
            loop = asyncio.get_event_loop()
            
            tenancy = await loop.run_in_executor(
                None,
                lambda: identity_client.get_tenancy(self.config['tenancy'])
            )
            
            logger.info(f"✅ OCI connection test successful. Tenancy: {tenancy.data.name}")
            return True
            
        except Exception as test_error:
            logger.warning(f"⚠️ OCI connection test failed: {test_error}")
            logger.warning("🔄 Will use mock data for development")
            return False

    async def _make_oci_call(self, client_method, *args, **kwargs):
        """Make OCI API call with retry logic"""
        try:
            # Create a wrapper function to handle kwargs properly
            def call_with_kwargs():
                return client_method(*args, **kwargs)
            
            return await asyncio.get_event_loop().run_in_executor(
                None, call_with_kwargs
            )
        except oci.exceptions.ServiceError as e:
            logger.error(f"OCI API error: {e}")
            raise ExternalServiceError(f"OCI API call failed: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error in OCI call: {e}")
            raise ExternalServiceError("OCI service temporarily unavailable")

    async def get_compartments(self) -> List[Dict[str, Any]]:
        """Get all accessible compartments"""
        cache_key = "oci:compartments"
        cached = self.cache.get(cache_key)
        if cached:
            logger.info(f"📦 Returning {len(cached)} compartments from cache")
            return cached
        
        try:
            if not self.oci_available:
                logger.info("OCI unavailable - returning dummy compartments")
                mock_compartments = [
                    {"id": "ocid1.tenancy.oc1..dummyroot", "name": "Root Tenancy", "description": "Root tenancy compartment", "lifecycle_state": "ACTIVE"},
                    {"id": "ocid1.compartment.oc1..prod", "name": "production", "description": "Production compartment", "lifecycle_state": "ACTIVE", "compartment_id": "ocid1.tenancy.oc1..dummyroot"},
                    {"id": "ocid1.compartment.oc1..stg", "name": "staging", "description": "Staging compartment", "lifecycle_state": "ACTIVE", "compartment_id": "ocid1.tenancy.oc1..dummyroot"},
                    {"id": "ocid1.compartment.oc1..dev", "name": "development", "description": "Development compartment", "lifecycle_state": "ACTIVE", "compartment_id": "ocid1.tenancy.oc1..dummyroot"}
                ]
                self.cache.set(cache_key, mock_compartments, 600)
                return mock_compartments
            
            logger.info("🔍 Fetching real compartments from OCI...")
            tenancy_id = self.config.get('tenancy')
            
            # Use the same working pattern as our test script
            # Get all compartments in tenancy (including root)
            response = await self._make_oci_call(
                self.clients['identity'].list_compartments,
                tenancy_id,
                compartment_id_in_subtree=True
            )
            
            compartments = []
            seen_ids = set()  # Track compartment IDs to prevent duplicates
            
            # First, add the tenancy itself as the root compartment
            compartments.append({
                "id": tenancy_id,
                "name": "Root Tenancy",
                "description": "Root tenancy compartment",
                "lifecycle_state": "ACTIVE"
                # No compartment_id = this is the true root
            })
            seen_ids.add(tenancy_id)
            
            # Then add all discovered compartments from OCI API
            for comp in response.data:
                # Skip duplicates
                if comp.id in seen_ids:
                    logger.warning(f"⚠️  Skipping duplicate compartment: {comp.name} ({comp.id})")
                    continue
                    
                seen_ids.add(comp.id)
                
                # Improve root tenancy naming for clarity
                comp_name = comp.name
                if comp.id == tenancy_id or not comp.compartment_id:
                    comp_name = "Root Tenancy" if comp.name == "(root)" else comp.name
                
                compartments.append({
                    "id": comp.id,
                    "name": comp_name,
                    "description": comp.description or "No description",
                    "lifecycle_state": comp.lifecycle_state,
                    "compartment_id": comp.compartment_id,  # Parent compartment
                    "time_created": comp.time_created.isoformat() if comp.time_created else None
                })
            
            logger.info(f"✅ Retrieved {len(compartments)} unique compartments from OCI")
            self.cache.set(cache_key, compartments, 600)  # 10 minutes cache
            return compartments
            
        except Exception as e:
            logger.error(f"❌ Failed to get compartments: {e}")
            # Fallback to mock data on error
            logger.warning("🔄 Falling back to simple mock compartment due to error")
            mock_compartments = [
                {
                    "id": "ocid1.compartment.oc1..error1",
                    "name": "Error-Fallback",
                    "description": "Fallback compartment due to API error",
                    "lifecycle_state": "ACTIVE"
                }
            ]
            return mock_compartments

    async def get_compute_instances(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get compute instances in a compartment"""
        cache_key = f"oci:compute:{compartment_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available or 'compute' not in self.clients:
                logger.info("OCI compute unavailable - returning dummy compute instances")
                instances = [
                    {"id": "ocid1.instance.oc1..vm1", "display_name": "prod-web-1", "lifecycle_state": "RUNNING", "shape": "VM.Standard3.Flex", "availability_domain": "AD-1", "time_created": datetime.utcnow().isoformat(), "region": self.config.get('region', 'eu-frankfurt-1')},
                    {"id": "ocid1.instance.oc1..vm2", "display_name": "prod-db-1", "lifecycle_state": "STOPPED", "shape": "VM.Standard3.Flex", "availability_domain": "AD-1", "time_created": datetime.utcnow().isoformat(), "region": self.config.get('region', 'eu-frankfurt-1')},
                    {"id": "ocid1.instance.oc1..vm3", "display_name": "stg-api-1", "lifecycle_state": "RUNNING", "shape": "VM.Standard.E4.Flex", "availability_domain": "AD-2", "time_created": datetime.utcnow().isoformat(), "region": self.config.get('region', 'eu-frankfurt-1')}
                ]
                self.cache.set(cache_key, instances, 300)
                return instances
            
            response = await self._make_oci_call(
                self.clients['compute'].list_instances,
                compartment_id
            )
            
            instances = []
            for instance in response.data:
                instances.append({
                    "id": instance.id,
                    "display_name": instance.display_name,
                    "lifecycle_state": instance.lifecycle_state,
                    "shape": instance.shape,
                    "availability_domain": instance.availability_domain,
                    "time_created": instance.time_created.isoformat() if instance.time_created else None,
                    "region": instance.region if hasattr(instance, 'region') else self.config.get('region')
                })
            
            self.cache.set(cache_key, instances, 300)  # 5 minutes cache
            return instances
            
        except Exception as e:
            logger.error(f"Failed to get compute instances: {e}")
            # Return empty list instead of raising exception to prevent frontend crashes
            return []

    async def get_databases(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get database services in a compartment (both DB Systems and Autonomous Databases)"""
        cache_key = f"oci:databases:{compartment_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available or 'database' not in self.clients:
                logger.info("OCI database unavailable - returning dummy database resources")
                databases = [
                    {"id": "ocid1.dbsystem.oc1..dbsys1", "display_name": "prod-db-system", "lifecycle_state": "AVAILABLE", "database_edition": "ENTERPRISE_EDITION_HIGH_PERFORMANCE", "shape": "VM.Standard2.2", "cpu_core_count": 4, "data_storage_size_in_gbs": 512, "node_count": 2, "availability_domain": "AD-1", "resource_type": "DB_SYSTEM", "time_created": datetime.utcnow().isoformat()},
                    {"id": "ocid1.database.oc1..db1", "display_name": "  └─ PRODDB (Database)", "db_name": "PRODDB", "lifecycle_state": "AVAILABLE", "db_workload": "OLTP", "character_set": "AL32UTF8", "pdb_name": None, "is_cdb": False, "resource_type": "DATABASE", "db_system_id": "ocid1.dbsystem.oc1..dbsys1", "db_home_id": "ocid1.dbhome.oc1..dbh1", "time_created": datetime.utcnow().isoformat()},
                    {"id": "ocid1.autonomousdatabase.oc1..adb1", "db_name": "ADWPROD", "display_name": "prod-adb", "lifecycle_state": "AVAILABLE", "db_workload": "DW", "cpu_core_count": 2, "data_storage_size_in_tbs": 1, "resource_type": "AUTONOMOUS_DATABASE", "time_created": datetime.utcnow().isoformat()}
                ]
                self.cache.set(cache_key, databases, 300)
                return databases
            
            databases = []
            
            # Get Database Systems (VM and Bare Metal DB systems)
            try:
                db_systems_response = await self._make_oci_call(
                    self.clients['database'].list_db_systems,
                    compartment_id=compartment_id
                )
                
                for db_system in db_systems_response.data:
                    databases.append({
                        "id": db_system.id,
                        "display_name": db_system.display_name,
                        "lifecycle_state": db_system.lifecycle_state,
                        "database_edition": getattr(db_system, 'database_edition', 'Unknown'),
                        "shape": getattr(db_system, 'shape', 'Unknown'),
                        "cpu_core_count": getattr(db_system, 'cpu_core_count', 0),
                        "data_storage_size_in_gbs": getattr(db_system, 'data_storage_size_in_gbs', 0),
                        "node_count": getattr(db_system, 'node_count', 1),
                        "availability_domain": getattr(db_system, 'availability_domain', 'Unknown'),
                        "resource_type": "DB_SYSTEM",
                        "time_created": db_system.time_created.isoformat() if db_system.time_created else None
                    })
                    
                    # Get DB Homes within each DB system, then databases within each DB Home
                    try:
                        # First get DB Homes for this DB System
                        db_homes_response = await self._make_oci_call(
                            self.clients['database'].list_db_homes,
                            compartment_id=compartment_id,
                            db_system_id=db_system.id
                        )
                        
                        for db_home in db_homes_response.data:
                            # Then get databases within each DB Home
                            try:
                                databases_response = await self._make_oci_call(
                                    self.clients['database'].list_databases,
                                    compartment_id=compartment_id,
                                    db_home_id=db_home.id
                                )
                                
                                for db in databases_response.data:
                                    databases.append({
                                        "id": db.id,
                                        "display_name": f"  └─ {db.db_name} (Database)",
                                        "db_name": db.db_name,
                                        "lifecycle_state": db.lifecycle_state,
                                        "db_workload": getattr(db, 'db_workload', 'Unknown'),
                                        "character_set": getattr(db, 'character_set', 'Unknown'),
                                        "pdb_name": getattr(db, 'pdb_name', None),
                                        "is_cdb": getattr(db, 'is_cdb', False),
                                        "resource_type": "DATABASE",
                                        "db_system_id": db_system.id,
                                        "db_home_id": db_home.id,
                                        "time_created": db.time_created.isoformat() if db.time_created else None
                                    })
                            except Exception as db_error:
                                logger.warning(f"Failed to get databases for DB home {db_home.id}: {db_error}")
                                
                    except Exception as db_home_error:
                        logger.warning(f"Failed to get DB homes for DB system {db_system.id}: {db_home_error}")
                        
            except Exception as e:
                logger.warning(f"Failed to get DB systems: {e}")
            
            # Also get Autonomous Databases
            try:
                autonomous_response = await self._make_oci_call(
                    self.clients['database'].list_autonomous_databases,
                    compartment_id=compartment_id
                )
                
                for db in autonomous_response.data:
                    databases.append({
                        "id": db.id,
                        "db_name": getattr(db, 'db_name', 'Unknown'),
                        "display_name": db.display_name,
                        "lifecycle_state": db.lifecycle_state,
                        "db_workload": getattr(db, 'db_workload', 'Unknown'),
                        "cpu_core_count": getattr(db, 'cpu_core_count', 0),
                        "data_storage_size_in_tbs": getattr(db, 'data_storage_size_in_tbs', 0),
                        "resource_type": "AUTONOMOUS_DATABASE",
                        "time_created": db.time_created.isoformat() if db.time_created else None
                    })
            except Exception as e:
                logger.warning(f"Failed to get Autonomous databases: {e}")
            
            logger.info(f"Found {len(databases)} total database resources in compartment")
            self.cache.set(cache_key, databases, 300)
            return databases
            
        except Exception as e:
            logger.error(f"Failed to get databases: {e}")
            return []

    async def get_oke_clusters(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get OKE clusters in a compartment"""
        cache_key = f"oci:oke:{compartment_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available or 'container_engine' not in self.clients:
                logger.info("OCI container engine unavailable - returning dummy OKE clusters")
                clusters = [
                    {"id": "ocid1.cluster.oc1..oke1", "name": "prod-oke", "lifecycle_state": "ACTIVE", "kubernetes_version": "1.27.3", "vcn_id": "ocid1.vcn.oc1..vcn1"},
                    {"id": "ocid1.cluster.oc1..oke2", "name": "stg-oke", "lifecycle_state": "ACTIVE", "kubernetes_version": "1.26.6", "vcn_id": "ocid1.vcn.oc1..vcn2"}
                ]
                self.cache.set(cache_key, clusters, 300)
                return clusters
            
            response = await self._make_oci_call(
                self.clients['container_engine'].list_clusters,
                compartment_id
            )
            
            clusters = []
            for cluster in response.data:
                clusters.append({
                    "id": cluster.id,
                    "name": cluster.name,
                    "lifecycle_state": cluster.lifecycle_state,
                    "kubernetes_version": cluster.kubernetes_version,
                    "vcn_id": cluster.vcn_id
                })
            
            self.cache.set(cache_key, clusters, 300)
            return clusters
            
        except Exception as e:
            logger.error(f"Failed to get OKE clusters: {e}")
            # Return empty list instead of raising exception to prevent frontend crashes
            return []

    async def get_api_gateways(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get API Gateways in a compartment"""
        cache_key = f"oci:api_gateways:{compartment_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available or 'api_gateway' not in self.clients:
                logger.info("OCI API gateway unavailable - returning dummy gateways")
                gateways = [
                    {"id": "ocid1.apigateway.oc1..gw1", "display_name": "prod-gateway", "lifecycle_state": "ACTIVE", "hostname": "api.prod.example.com"},
                    {"id": "ocid1.apigateway.oc1..gw2", "display_name": "stg-gateway", "lifecycle_state": "ACTIVE", "hostname": "api.stg.example.com"}
                ]
                self.cache.set(cache_key, gateways, 300)
                return gateways
            
            response = await self._make_oci_call(
                self.clients['api_gateway'].list_gateways,
                compartment_id
            )
            
            gateways = []
            # Handle the GatewayCollection object properly
            gateway_list = response.data.items if hasattr(response.data, 'items') else response.data
            for gateway in gateway_list:
                gateways.append({
                    "id": gateway.id,
                    "display_name": gateway.display_name,
                    "lifecycle_state": gateway.lifecycle_state,
                    "hostname": getattr(gateway, 'hostname', 'N/A')
                })
            
            self.cache.set(cache_key, gateways, 300)
            return gateways
            
        except Exception as e:
            logger.error(f"Failed to get API gateways: {e}")
            # Return empty list instead of raising exception to prevent frontend crashes
            return []

    async def get_load_balancers(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get load balancers in a compartment"""
        cache_key = f"oci:load_balancers:{compartment_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available or 'load_balancer' not in self.clients:
                logger.info("OCI load balancer unavailable - returning dummy load balancers")
                load_balancers = [
                    {"id": "ocid1.loadbalancer.oc1..lb1", "display_name": "prod-lb", "lifecycle_state": "ACTIVE", "shape_name": "flexible", "is_private": False},
                    {"id": "ocid1.loadbalancer.oc1..lb2", "display_name": "stg-lb", "lifecycle_state": "ACTIVE", "shape_name": "flexible", "is_private": True}
                ]
                self.cache.set(cache_key, load_balancers, 300)
                return load_balancers
            
            response = await self._make_oci_call(
                self.clients['load_balancer'].list_load_balancers,
                compartment_id
            )
            
            load_balancers = []
            for lb in response.data:
                load_balancers.append({
                    "id": lb.id,
                    "display_name": lb.display_name,
                    "lifecycle_state": lb.lifecycle_state,
                    "shape_name": lb.shape_name,
                    "is_private": lb.is_private
                })
            
            self.cache.set(cache_key, load_balancers, 300)
            return load_balancers
            
        except Exception as e:
            logger.error(f"Failed to get load balancers: {e}")
            # Return empty list instead of raising exception to prevent frontend crashes
            return []

    async def get_network_resources(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get network resources (VCNs, subnets, etc.) in a compartment"""
        cache_key = f"oci:network:{compartment_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available or 'virtual_network' not in self.clients:
                logger.info("OCI virtual network unavailable - returning dummy VCNs and Subnets")
                networks = [
                    {"id": "ocid1.vcn.oc1..vcn1", "display_name": "prod-vcn", "lifecycle_state": "AVAILABLE", "cidr_block": "10.0.0.0/16", "resource_type": "VCN", "time_created": datetime.utcnow().isoformat()},
                    {"id": "ocid1.subnet.oc1..sub1", "display_name": "  └─ prod-subnet-a", "lifecycle_state": "AVAILABLE", "cidr_block": "10.0.1.0/24", "resource_type": "Subnet", "vcn_id": "ocid1.vcn.oc1..vcn1", "time_created": datetime.utcnow().isoformat()},
                    {"id": "ocid1.subnet.oc1..sub2", "display_name": "  └─ prod-subnet-b", "lifecycle_state": "AVAILABLE", "cidr_block": "10.0.2.0/24", "resource_type": "Subnet", "vcn_id": "ocid1.vcn.oc1..vcn1", "time_created": datetime.utcnow().isoformat()}
                ]
                self.cache.set(cache_key, networks, 300)
                return networks
            
            # Get VCNs
            vcn_response = await self._make_oci_call(
                self.clients['virtual_network'].list_vcns,
                compartment_id
            )
            
            networks = []
            for vcn in vcn_response.data:
                networks.append({
                    "id": vcn.id,
                    "display_name": vcn.display_name,
                    "lifecycle_state": vcn.lifecycle_state,
                    "cidr_block": vcn.cidr_block,
                    "resource_type": "VCN",
                    "time_created": vcn.time_created.isoformat() if vcn.time_created else None
                })
                
                # Get subnets for each VCN
                try:
                    subnet_response = await self._make_oci_call(
                        self.clients['virtual_network'].list_subnets,
                        compartment_id,
                        vcn_id=vcn.id
                    )
                    
                    for subnet in subnet_response.data:
                        networks.append({
                            "id": subnet.id,
                            "display_name": f"  └─ {subnet.display_name}",
                            "lifecycle_state": subnet.lifecycle_state,
                            "cidr_block": subnet.cidr_block,
                            "resource_type": "Subnet",
                            "vcn_id": vcn.id,
                            "time_created": subnet.time_created.isoformat() if subnet.time_created else None
                        })
                except Exception as e:
                    logger.warning(f"Failed to get subnets for VCN {vcn.id}: {e}")
            
            self.cache.set(cache_key, networks, 300)
            return networks
            
        except Exception as e:
            logger.error(f"Failed to get network resources: {e}")
            # Return empty list instead of raising exception to prevent frontend crashes
            return []

    async def get_block_volumes(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get block volumes in a compartment"""
        cache_key = f"oci:block_volumes:{compartment_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available or 'block_storage' not in self.clients:
                logger.info("OCI block storage unavailable - returning dummy volumes")
                volumes = [
                    {"id": "ocid1.volume.oc1..vol1", "display_name": "prod-volume-a", "lifecycle_state": "AVAILABLE", "size_in_gbs": 256, "availability_domain": "AD-1", "time_created": datetime.utcnow().isoformat()},
                    {"id": "ocid1.volume.oc1..vol2", "display_name": "prod-volume-b", "lifecycle_state": "AVAILABLE", "size_in_gbs": 512, "availability_domain": "AD-1", "time_created": datetime.utcnow().isoformat()}
                ]
                self.cache.set(cache_key, volumes, 300)
                return volumes
            
            response = await self._make_oci_call(
                self.clients['block_storage'].list_volumes,
                compartment_id=compartment_id
            )
            
            volumes = []
            for volume in response.data:
                volumes.append({
                    "id": volume.id,
                    "display_name": volume.display_name,
                    "lifecycle_state": volume.lifecycle_state,
                    "size_in_gbs": volume.size_in_gbs,
                    "availability_domain": volume.availability_domain,
                    "volume_group_id": getattr(volume, 'volume_group_id', None),
                    "is_hydrated": getattr(volume, 'is_hydrated', True),
                    "time_created": volume.time_created.isoformat() if volume.time_created else None
                })
            
            self.cache.set(cache_key, volumes, 300)
            return volumes
            
        except Exception as e:
            logger.error(f"Failed to get block volumes: {e}")
            return []

    async def get_file_systems(self, compartment_id: str) -> List[Dict[str, Any]]:
        """Get file systems in a compartment"""
        cache_key = f"oci:file_systems:{compartment_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available or 'file_storage' not in self.clients:
                logger.info("OCI file storage unavailable - returning dummy file systems")
                file_systems = [
                    {"id": "ocid1.filesystem.oc1..fs1", "display_name": "prod-fs-a", "lifecycle_state": "ACTIVE", "availability_domain": "AD-1", "metered_bytes": 123456789, "time_created": datetime.utcnow().isoformat()},
                    {"id": "ocid1.filesystem.oc1..fs2", "display_name": "prod-fs-b", "lifecycle_state": "ACTIVE", "availability_domain": "AD-1", "metered_bytes": 987654321, "time_created": datetime.utcnow().isoformat()}
                ]
                self.cache.set(cache_key, file_systems, 300)
                return file_systems
            
            # Get availability domains first
            identity_client = self.clients['identity']
            ads_response = await self._make_oci_call(
                identity_client.list_availability_domains,
                compartment_id=self.config['tenancy']
            )
            
            file_systems = []
            # Query file systems in each availability domain
            for ad in ads_response.data:
                try:
                    response = await self._make_oci_call(
                        self.clients['file_storage'].list_file_systems,
                        compartment_id=compartment_id,
                        availability_domain=ad.name
                    )
                    
                    for fs in response.data:
                        file_systems.append({
                            "id": fs.id,
                            "display_name": fs.display_name,
                            "lifecycle_state": fs.lifecycle_state,
                            "availability_domain": fs.availability_domain,
                            "metered_bytes": getattr(fs, 'metered_bytes', 0),
                            "source_details": getattr(fs, 'source_details', None),
                            "time_created": fs.time_created.isoformat() if fs.time_created else None
                        })
                except Exception as ad_error:
                    logger.warning(f"Failed to get file systems in AD {ad.name}: {ad_error}")
                    continue
            
            self.cache.set(cache_key, file_systems, 300)
            return file_systems
            
        except Exception as e:
            logger.error(f"Failed to get file systems: {e}")
            return []

    async def get_resource_metrics(self, resource_id: str, resource_type: str) -> Dict[str, Any]:
        """Get real-time metrics for a resource"""
        cache_key = f"oci:metrics:{resource_id}:{resource_type}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            if not self.oci_available or 'monitoring' not in self.clients:
                logger.info("OCI monitoring unavailable - returning dummy metrics")
                return {
                    "resource_id": resource_id,
                    "metrics": {
                        "cpu_utilization": 62.5,
                        "memory_utilization": 71.3,
                        "network_bytes_in": 12582912,
                        "network_bytes_out": 10485760
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "health_status": "HEALTHY"
                }
            
            # Query OCI monitoring service for real metrics
            # This is a simplified implementation - real metrics would require specific queries
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            metrics_data = {
                "resource_id": resource_id,
                "metrics": {
                    "cpu_utilization": 0.0,
                    "memory_utilization": 0.0, 
                    "network_bytes_in": 0,
                    "network_bytes_out": 0
                },
                "timestamp": end_time.isoformat(),
                "health_status": "UNKNOWN"
            }
            
            self.cache.set(cache_key, metrics_data, 60)
            return metrics_data
            
        except Exception as e:
            logger.error(f"Failed to get metrics for {resource_id}: {e}")
            raise ExternalServiceError("Unable to retrieve resource metrics")

    async def get_all_resources(self, compartment_id: str, resource_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get all resources in a compartment with optional filtering"""
        try:
            # If compartment_id is a tenancy root, query all compartments
            is_tenancy_root = compartment_id == self.config.get('tenancy') if self.config else False
            
            if is_tenancy_root:
                logger.info("🔍 Querying all compartments for resources...")
                return await self._get_all_resources_from_all_compartments(resource_filter)
            else:
                logger.info(f"🔍 Querying single compartment for resources: {compartment_id}")
                return await self._get_all_resources_from_single_compartment(compartment_id, resource_filter)
            
        except Exception as e:
            logger.error(f"Failed to get all resources: {e}")
            raise ExternalServiceError("Unable to retrieve compartment resources")

    async def _get_all_resources_from_all_compartments(self, resource_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get resources from all compartments in the tenancy - TENANCY AGNOSTIC"""
        try:
            # Get all compartments
            compartments = await self.get_compartments()
            logger.info(f"Found {len(compartments)} compartments to query")
            
            # Get the appropriate methods
            method_map = {
                'compute_instances': self.get_compute_instances,
                'databases': self.get_databases,
                'oke_clusters': self.get_oke_clusters,
                'api_gateways': self.get_api_gateways,
                'load_balancers': self.get_load_balancers,
                'network_resources': self.get_network_resources,
                'block_volumes': self.get_block_volumes,
                'file_systems': self.get_file_systems
            }
            
            # Initialize aggregated results
            aggregated_results = {resource_type: [] for resource_type in method_map.keys()}
            
            # Query ALL compartments for ALL resource types (tenancy agnostic approach)
            for comp in compartments:
                comp_name = comp['name']
                comp_id = comp['id']
                
                logger.info(f"Querying compartment: {comp_name}")
                
                for resource_type, method in method_map.items():
                    if resource_filter and resource_type not in resource_filter:
                        continue
                    
                    try:
                        resources = await method(comp_id)
                        if resources:
                            # Add compartment info to each resource for tracking
                            for resource in resources:
                                resource['source_compartment'] = comp_name
                                
                            aggregated_results[resource_type].extend(resources)
                            logger.info(f"Found {len(resources)} {resource_type} in {comp_name}")
                            
                    except Exception as e:
                        # Log but don't fail - some compartments may not have permissions for certain resources
                        logger.debug(f"Could not query {resource_type} from {comp_name}: {e}")
            
            # Summary logging
            total_resources = sum(len(resources) for resources in aggregated_results.values())
            logger.info(f"Total resources found across all compartments: {total_resources}")
            
            for resource_type, resources in aggregated_results.items():
                if resources:
                    logger.info(f"  {resource_type}: {len(resources)} resources")
            
            return {
                "compartment_id": "all_compartments",
                "resources": aggregated_results,
                "total_resources": total_resources,
                "last_updated": datetime.utcnow().isoformat(),
                "compartments_queried": len(compartments)
            }
            
        except Exception as e:
            logger.error(f"Failed to get resources from all compartments: {e}")
            raise

    async def _get_all_resources_from_single_compartment(self, compartment_id: str, resource_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get all resources from a single compartment"""
        # Get all resource types in parallel
        tasks = []
        
        if not resource_filter or 'compute_instances' in resource_filter:
            tasks.append(('compute_instances', self.get_compute_instances(compartment_id)))
        
        if not resource_filter or 'databases' in resource_filter:
            tasks.append(('databases', self.get_databases(compartment_id)))
        
        if not resource_filter or 'oke_clusters' in resource_filter:
            tasks.append(('oke_clusters', self.get_oke_clusters(compartment_id)))
        
        if not resource_filter or 'api_gateways' in resource_filter:
            tasks.append(('api_gateways', self.get_api_gateways(compartment_id)))
        
        if not resource_filter or 'load_balancers' in resource_filter:
            tasks.append(('load_balancers', self.get_load_balancers(compartment_id)))
        
        if not resource_filter or 'network_resources' in resource_filter:
            tasks.append(('network_resources', self.get_network_resources(compartment_id)))
        
        if not resource_filter or 'block_volumes' in resource_filter:
            tasks.append(('block_volumes', self.get_block_volumes(compartment_id)))
        
        if not resource_filter or 'file_systems' in resource_filter:
            tasks.append(('file_systems', self.get_file_systems(compartment_id)))
        
        # Execute all tasks in parallel
        results = {}
        for name, task in tasks:
            try:
                results[name] = await task
            except Exception as e:
                logger.error(f"Failed to get {name}: {e}")
                results[name] = []
        
        return {
            "compartment_id": compartment_id,
            "resources": results,
            "total_resources": sum(len(resources) for resources in results.values()),
            "last_updated": datetime.utcnow().isoformat()
        }

# Legacy CloudOperationsService for backward compatibility
class CloudOperationsService:
    """Legacy service wrapper for backward compatibility"""
    
    def __init__(self):
        self.oci_service = OCIService()
    
    async def get_cloud_resources(self, provider: str = "oci", compartment_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cloud resources (wrapper for legacy compatibility)"""
        if provider != "oci":
            raise ExternalServiceError(f"Provider {provider} not supported")
        
        try:
            if not compartment_id:
                # Get first available compartment
                compartments = await self.oci_service.get_compartments()
                if not compartments:
                    raise ExternalServiceError("No accessible compartments found")
                compartment_id = compartments[0]['id']
            
            return await self.oci_service.get_all_resources(compartment_id)
            
        except Exception as e:
            logger.error(f"Failed to get cloud resources: {e}")
            raise ExternalServiceError("Cloud resources unavailable")

# Service instances
oci_service = OCIService()
cloud_ops_service = CloudOperationsService()

# For backward compatibility
k8s_service = None  # Will be implemented separately if needed 