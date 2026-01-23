# backend/app/services/sessions.py

from fastapi import  HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase # Importar AsyncIOMotorDatabase
from datetime import datetime, timezone
from bson import ObjectId
from db.db import get_database, db as data, db as database_instance 
from  schemas.sessions  import SessionOut, Session
from typing import Optional


# Nombre de la colección de sesiones
SESSIONS_COLLECTION = "sessions"

async def start_session(db: AsyncIOMotorClient, user_id: str) -> SessionOut:
    """
    Crea un nuevo registro de sesión en la base de datos.
    """
    session_data = {
        "user_id": user_id,
        "start_time": datetime.utcnow(),
    }

    # Insertar el nuevo documento en la colección
    result = await db[SESSIONS_COLLECTION].insert_one(session_data)
    
    # Verificar si la inserción fue exitosa
    if not result.inserted_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al iniciar la sesión en la base de datos"
        )
    
    # Recuperar el documento recién creado para asegurar la estructura de SessionOut
    new_session_doc = await db[SESSIONS_COLLECTION].find_one({"_id": result.inserted_id})

    # Usar el esquema de respuesta para la serialización
    return SessionOut(
        id=str(new_session_doc["_id"]),
        user_id=new_session_doc["user_id"],
        start_time=new_session_doc["start_time"]
    )

async def end_session(db: AsyncIOMotorDatabase, session_id: str, user_id: str) -> SessionOut:
    """
    Finaliza una sesión de estudio, registra el tiempo y calcula la duración.
    """
    if not ObjectId.is_valid(session_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de sesión inválido."
        )

    session_oid = ObjectId(session_id)
    
    # 1. Buscar la sesión y verificar que pertenezca al usuario y que no haya terminado
    session_doc = await db[SESSIONS_COLLECTION].find_one({"_id": session_oid, "user_id": user_id})

    if not session_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada o no pertenece al usuario."
        )
        
    if session_doc.get("end_time"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La sesión ya ha sido finalizada."
        )

    # 2. Calcular la duración
    end_time = datetime.now(timezone.utc)
    start_time = session_doc["start_time"].replace(tzinfo=timezone.utc)
    
    # Usamos total_seconds() para obtener la diferencia en segundos
    duration_seconds = (end_time - start_time).total_seconds()
    duration_minutes = round(duration_seconds / 60, 2)

    # 3. Actualizar el documento en MongoDB
    update_data = {
        "end_time": end_time,
        "duration_minutes": duration_minutes
    }

    result = await db[SESSIONS_COLLECTION].update_one(
        {"_id": session_oid},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar la sesión."
        )
    
    # 4. Devolver la sesión actualizada
    updated_session_doc = await db[SESSIONS_COLLECTION].find_one({"_id": session_oid})

    # Convertimos el documento completo al esquema SessionOut para la respuesta
    return SessionOut(
        id=str(updated_session_doc["_id"]),
        user_id=updated_session_doc["user_id"],
        start_time=updated_session_doc["start_time"],
        end_time=updated_session_doc.get("end_time"), # Incluimos el nuevo campo
        duration_minutes=updated_session_doc.get("duration_minutes") # Incluimos el nuevo campo
    )