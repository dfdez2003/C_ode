# backend/app/routers/sessions.py

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase # Importar el tipo de dato correcto
from db.db import get_database # ✨ Esta es la función que debe usarse en Depends
from services.sessions import start_session, end_session
from utils.user import get_current_user
from schemas.sessions import SessionOut
from schemas.users import UserResponse


router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
)
# ---------- Rutas de gestión de sesiones de estudio ---------- #
# Iniciar una nueva sesión de estudio
@router.post("/start", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def start_study_session(
    db: AsyncIOMotorDatabase = Depends(get_database), 
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Inicia una nueva sesión de estudio para el usuario autenticado.
    """
    try:
        session = await start_session(db, current_user.id)
        return session
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al iniciar la sesión: {str(e)}"
        )
    
# Finalizar una sesión de estudio existente
@router.put("/{session_id}/end", response_model=SessionOut, status_code=status.HTTP_200_OK)
async def end_study_session(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Finaliza una sesión de estudio. Requiere el ID de la sesión en la URL.
    Actualiza end_time y calcula la duración.
    """
    try:
        session = await end_session(db, session_id, current_user.id)
        return session
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al finalizar la sesión: {str(e)}"
        )