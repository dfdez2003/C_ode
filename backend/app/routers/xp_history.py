"""
Endpoints para consultar el historial de XP del usuario.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from services.xp_history import XPHistoryService
from db.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/xp-history", tags=["XP History"])

@router.get("/user/{user_id}/history")
async def get_user_xp_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Obtiene el historial de XP de un usuario.
    
    Parámetros:
    - user_id: ID del usuario
    - limit: Número máximo de registros (1-100, default 50)
    - skip: Registros a saltar para paginación (default 0)
    
    Retorna lista de transacciones de XP ordenadas por fecha descendente.
    """
    try:
        history = await XPHistoryService.get_user_xp_history(db, user_id, limit, skip)
        return {
            "user_id": user_id,
            "count": len(history),
            "limit": limit,
            "skip": skip,
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/summary")
async def get_user_xp_summary(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Obtiene un resumen del XP del usuario.
    
    Retorna:
    {
        "total_xp": total XP acumulado,
        "total_transactions": número de transacciones,
        "breakdown_by_reason": {
            "lesson_completion": 5,
            "perfection_bonus": 3,
            "reward_awarded": 2,
            ...
        }
    }
    """
    try:
        summary = await XPHistoryService.get_xp_summary(db, user_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
