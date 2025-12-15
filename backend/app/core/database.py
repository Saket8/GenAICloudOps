from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG  # Enable SQL logging in debug mode
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    """Create all database tables"""
    from app.models.user import Base as UserBase
    from app.models.remediation import Base as RemediationBase
    from app.models.chatbot import Base as ChatbotBase
    
    # Create all tables from all models
    UserBase.metadata.create_all(bind=engine)
    RemediationBase.metadata.create_all(bind=engine)
    ChatbotBase.metadata.create_all(bind=engine)

# Initialize default roles
def init_default_roles():
    """Initialize default roles in database"""
    from sqlalchemy.orm import Session
    from app.models.user import Role, RoleEnum
    
    db = SessionLocal()
    try:
        # Define all default roles
        default_roles = [
            Role(
                name=RoleEnum.ADMIN,
                display_name="Administrator",
                description="Full access to all features and user management",
                can_view_dashboard=True,
                can_view_alerts=True,
                can_approve_remediation=True,
                can_execute_remediation=True,
                can_manage_users=True,
                can_manage_roles=True,
                can_view_access_analyzer=True,
                can_view_pod_analyzer=True,
                can_view_cost_analyzer=True,
                can_use_chatbot=True
            ),
            Role(
                name=RoleEnum.OPERATOR,
                display_name="Operator",
                description="Can view, analyze and approve/execute remediations",
                can_view_dashboard=True,
                can_view_alerts=True,
                can_approve_remediation=True,
                can_execute_remediation=True,
                can_manage_users=False,
                can_manage_roles=False,
                can_view_access_analyzer=True,
                can_view_pod_analyzer=True,
                can_view_cost_analyzer=True,
                can_use_chatbot=True
            ),
            Role(
                name=RoleEnum.VIEWER,
                display_name="Viewer",
                description="Read-only access to dashboards and analytics",
                can_view_dashboard=True,
                can_view_alerts=True,
                can_approve_remediation=False,
                can_execute_remediation=False,
                can_manage_users=False,
                can_manage_roles=False,
                can_view_access_analyzer=True,
                can_view_pod_analyzer=True,
                can_view_cost_analyzer=True,
                can_use_chatbot=True
            ),
            Role(
                name=RoleEnum.CLOUD_ADMIN,
                display_name="Infrastructure Admin",
                description="Access to Cloud Infrastructure (OCI/AWS)",
                can_view_dashboard=True,
                can_view_alerts=True,
                can_approve_remediation=False,
                can_execute_remediation=False,
                can_manage_users=False,
                can_manage_roles=False,
                can_view_access_analyzer=False,
                can_view_pod_analyzer=False,
                can_view_cost_analyzer=True,
                can_use_chatbot=True
            ),
            Role(
                name=RoleEnum.APP_ADMIN,
                display_name="Application Admin",
                description="Access to Application Monitoring",
                can_view_dashboard=True,
                can_view_alerts=True,
                can_approve_remediation=False,
                can_execute_remediation=False,
                can_manage_users=False,
                can_manage_roles=False,
                can_view_access_analyzer=False,
                can_view_pod_analyzer=True,
                can_view_cost_analyzer=False,
                can_use_chatbot=True
            ),
            Role(
                name=RoleEnum.SECURITY_ADMIN,
                display_name="Security Admin",
                description="Access to Security Monitoring",
                can_view_dashboard=True,
                can_view_alerts=True,
                can_approve_remediation=True,
                can_execute_remediation=True,
                can_manage_users=False,
                can_manage_roles=False,
                can_view_access_analyzer=True,
                can_view_pod_analyzer=False,
                can_view_cost_analyzer=False,
                can_use_chatbot=True
            ),
            Role(
                name=RoleEnum.SYS_ADMIN,
                display_name="System Admin",
                description="Access to User Management and Settings",
                can_view_dashboard=True,
                can_view_alerts=False,
                can_approve_remediation=False,
                can_execute_remediation=False,
                can_manage_users=True,
                can_manage_roles=True,
                can_view_access_analyzer=False,
                can_view_pod_analyzer=False,
                can_view_cost_analyzer=False,
                can_use_chatbot=False
            )
        ]
        
        for role in default_roles:
            existing = db.query(Role).filter(Role.name == role.name).first()
            if not existing:
                db.add(role)
                print(f"Created role: {role.name}")
            else:
                # Update existing role with correct permissions
                existing.display_name = role.display_name
                existing.description = role.description
                existing.can_view_dashboard = role.can_view_dashboard
                existing.can_view_alerts = role.can_view_alerts
                existing.can_approve_remediation = role.can_approve_remediation
                existing.can_execute_remediation = role.can_execute_remediation
                existing.can_manage_users = role.can_manage_users
                existing.can_manage_roles = role.can_manage_roles
                existing.can_view_access_analyzer = role.can_view_access_analyzer
                existing.can_view_pod_analyzer = role.can_view_pod_analyzer
                existing.can_view_cost_analyzer = role.can_view_cost_analyzer
                existing.can_use_chatbot = role.can_use_chatbot
                print(f"Updated role: {role.name}")
        
        db.commit()
        print("Default roles initialized successfully")
        
    except Exception as e:
        db.rollback()
        print(f"Error initializing roles: {e}")
    finally:
        db.close()