from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Schema para crear una recompensa
class RewardCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Título de la recompensa")
    description: str = Field(..., min_length=1, max_length=500, description="Descripción de la recompensa")
    icon: str = Field(default="🎁", description="Emoji o ícono de la recompensa")
    reward_type: str = Field(..., description="Tipo: lesson_perfect, streak_milestone, xp_milestone, custom")
    criteria: Optional[Dict[str, Any]] = Field(default=None, description="Criterios específicos del tipo de recompensa")
    xp_bonus: int = Field(..., ge=1, description="Puntos XP otorgados al obtener la recompensa (mínimo 1)")
    is_active: bool = Field(default=True, description="Si la recompensa está activa")


# Schema para actualizar una recompensa (todos opcionales)
class RewardUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    icon: Optional[str] = None
    reward_type: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None
    xp_bonus: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


# Schema de respuesta (alias RewardResponse para compatibilidad)
class RewardResponse(BaseModel):
    id: str = Field(alias="_id")
    title: str
    description: str
    icon: str
    reward_type: str
    criteria: Optional[Dict[str, Any]] = None
    xp_bonus: int
    is_active: bool
    users_awarded: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        populate_by_name = True


# Alias para mantener ambos nombres
RewardOut = RewardResponse


class RewardListResponse(BaseModel):
    """Schema para respuesta de lista de recompensas"""
    total: int
    rewards: List[RewardResponse]


# Schemas legacy (mantener compatibilidad con endpoints existentes)
class RewardIn(BaseModel):
    name: str
    description: str
    type: str
    points: int

class RewardOutLegacy(RewardIn):
    id: str
    users_awarded: List[str]

    