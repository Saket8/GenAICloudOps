from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class RoleBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    
    # Permissions
    can_view_dashboard: bool = True
    can_view_alerts: bool = True
    can_approve_remediation: bool = False
    can_execute_remediation: bool = False
    can_manage_users: bool = False
    can_manage_roles: bool = False
    can_view_access_analyzer: bool = True
    can_view_pod_analyzer: bool = True
    can_view_cost_analyzer: bool = True
    can_use_chatbot: bool = True

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    
    # Permissions
    can_view_dashboard: Optional[bool] = None
    can_view_alerts: Optional[bool] = None
    can_approve_remediation: Optional[bool] = None
    can_execute_remediation: Optional[bool] = None
    can_manage_users: Optional[bool] = None
    can_manage_roles: Optional[bool] = None
    can_view_access_analyzer: Optional[bool] = None
    can_view_pod_analyzer: Optional[bool] = None
    can_view_cost_analyzer: Optional[bool] = None
    can_use_chatbot: Optional[bool] = None

class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
