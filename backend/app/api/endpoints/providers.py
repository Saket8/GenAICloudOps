from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

from app.core.config import settings

router = APIRouter()


class CloudProvider(BaseModel):
    id: str
    name: str
    description: str
    region_defaults: Dict[str, Any]
    features: Dict[str, bool]
    status: str


@router.get("/", response_model=List[CloudProvider])
async def list_cloud_providers() -> List[CloudProvider]:
    providers: List[Dict[str, Any]] = [
        {
            "id": "oci",
            "name": "Oracle Cloud Infrastructure",
            "description": "Existing GenAI CloudOps implementation for OCI",
            "region_defaults": {"primary": settings.OCI_REGION},
            "features": {
                "monitoring": True,
                "cost_analysis": True,
                "security_analysis": True,
                "automation": True,
                "chatbot": True,
            },
            "status": "available",
        }
    ]

    providers.append(
        {
            "id": "aws",
            "name": "Amazon Web Services",
            "description": "Demo-mode AWS prototype with parallel features",
            "region_defaults": {"primary": settings.AWS_DEFAULT_REGION},
            "features": {
                "monitoring": True,
                "cost_analysis": True,
                "security_analysis": True,
                "automation": True,
                "chatbot": False,
            },
            "status": "preview" if settings.USE_DUMMY_AWS else "beta",
        }
    )

    return [CloudProvider(**provider) for provider in providers]
