# backend/app/schemas/sessions.py

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId

# Reutilizamos la implementación de PyObjectId centralizada en `models.py`
from models import PyObjectId


# Esquema de la sesión tal como se guarda en la DB (Pydantic v2 style)
class Session(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId = Field(..., description="ID del usuario logueado")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Momento de inicio de la sesión")
    end_time: Optional[datetime] = Field(default=None, description="Momento de finalización de la sesión")
    duration_minutes: Optional[float] = Field(default=None, description="Duración total de la sesión")

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "_id": "60c72b1f9b3e6c3a1d9b3e6c",
                "user_id": "60c72b1f9b3e6c3a1d9b3e6c",
                "start_time": "2025-01-01T10:00:00Z"
            }
        }
    }


# Esquema de respuesta de la API
class SessionOut(BaseModel):
    id: str = Field(..., description="ID de la sesión creada")
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "60c72b1f9b3e6c3a1d9b3e6c",
                "user_id": "60c72b1f9b3e6c3a1d9b3e6c",
                "start_time": "2025-01-01T10:00:00Z"
            }
        }
    }