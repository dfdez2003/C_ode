# routers/rewards.py

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.db import get_database
from schemas.users import UserResponse
from schemas.rewards import RewardCreate, RewardUpdate, RewardResponse
from utils.user import get_current_user, require_teacher_role
from services.rewards import create_reward_service, update_reward_service, delete_reward_service
from bson import ObjectId
from typing import List, Dict, Any

router = APIRouter(prefix="/rewards", tags=["Rewards"])

REWARDS_COLLECTION = "rewards"

# ========== RUTAS PÚBLICAS DE RECOMPENSAS ==========
# Estas rutas son accesibles para estudiantes y profesores

# ----- Función auxiliar para normalizar recompensas ----- #    
def _normalize_reward(reward: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza un documento de recompensa:
    - Convierte ObjectIds a strings
    - Asegura que xp_bonus siempre existe (usa points como fallback)
    """
    reward["_id"] = str(reward["_id"])
    reward["users_awarded"] = [str(uid) for uid in reward.get("users_awarded", [])]
    
    # Normalizar xp_bonus: si no existe, usar points (para compatibilidad con datos antiguos)
    if "xp_bonus" not in reward and "points" in reward:
        reward["xp_bonus"] = reward.get("points", 0)
    elif "xp_bonus" not in reward:
        reward["xp_bonus"] = 0
    
    return reward

# ---------- Rutas de recompensas ---------- #
@router.get("/", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_all_rewards(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtiene todas las recompensas disponibles en el sistema.
    
    Devuelve:
    - Lista de todas las recompensas con sus detalles
    - Incluye el campo users_awarded con los IDs de usuarios que ya la obtuvieron
    """
    cursor = db[REWARDS_COLLECTION].find()
    rewards = await cursor.to_list(length=None)
    
    # Normalizar cada recompensa
    rewards = [_normalize_reward(reward) for reward in rewards]
    
    return rewards

# ---------- Rutas de recompensas por usuario ---------- #
@router.get("/user/{user_id}", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_user_rewards(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtiene todas las recompensas que un usuario específico ha desbloqueado.
    
    Seguridad:
    - Un estudiante solo puede ver sus propias recompensas
    - Un profesor puede ver recompensas de cualquier usuario
    """
    # Verificar permisos
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver las recompensas de otros usuarios."
        )
    
    # Validar ObjectId
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido."
        )
    
    user_oid = ObjectId(user_id)
    
    # Buscar recompensas donde el usuario está en users_awarded
    cursor = db[REWARDS_COLLECTION].find({
        "users_awarded": user_oid
    })
    
    user_rewards = await cursor.to_list(length=None)
    
    # Normalizar cada recompensa
    user_rewards = [_normalize_reward(reward) for reward in user_rewards]
    
    return user_rewards

# ---------- Rutas de recompensas disponibles ---------- #
@router.get("/available/{user_id}", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_available_rewards(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtiene las recompensas que un usuario AÚN NO ha obtenido pero PUEDE obtener.
    Muestra progreso hacia cada una.
    
    Por ejemplo:
    - XP milestone: muestra XP actual vs requerido
    - Streak milestone: muestra racha actual vs requerida
    - Lesson perfect: muestra si está disponible
    """
    # Verificar permisos
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esto."
        )
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido."
        )
    
    user_oid = ObjectId(user_id)
    
    # Obtener datos del usuario (XP, racha, etc)
    user = await db["users"].find_one({"_id": user_oid})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    
    current_xp = user.get("total_points", 0)
    current_streak = user.get("current_streak", 0)
    
    # Obtener todas las recompensas activas que el usuario AÚN NO tiene
    cursor = db[REWARDS_COLLECTION].find({
        "is_active": True,
        "users_awarded": {"$ne": user_oid}
    })
    
    available = await cursor.to_list(length=None)
    
    # Procesar cada recompensa para agregar progreso
    result = []
    for reward in available:
        reward = _normalize_reward(reward)
        
        # Agregar información de progreso según tipo
        if reward["reward_type"] == "xp_milestone":
            threshold = reward.get("criteria", {}).get("xp_threshold", 0)
            reward["progress"] = {
                "current": current_xp,
                "required": threshold,
                "percentage": min(100, (current_xp / threshold * 100) if threshold > 0 else 100)
            }
        elif reward["reward_type"] == "streak_milestone":
            required = reward.get("criteria", {}).get("streak", 0)
            reward["progress"] = {
                "current": current_streak,
                "required": required,
                "percentage": min(100, (current_streak / required * 100) if required > 0 else 100)
            }
        
        result.append(reward)
    
    return result

# ---------- Rutas de recompensas del usuario actual ---------- #
@router.get("/available", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_available_rewards(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtiene todas las recompensas que el usuario actual aun no ha desbloqueado.
    
    Útil para mostrar en el frontend qué logros quedan por conseguir.
    """
    user_oid = ObjectId(current_user.id)
    
    # Buscar recompensas donde el usuario NO está en users_awarded
    cursor = db[REWARDS_COLLECTION].find({
        "users_awarded": {"$ne": user_oid}
    })
    
    available_rewards = await cursor.to_list(length=None)
    
    # Convertir ObjectIds a strings
    for reward in available_rewards:
        reward["_id"] = str(reward["_id"])
        reward["users_awarded"] = [str(uid) for uid in reward.get("users_awarded", [])]
    
    return available_rewards

# ---------- Estadísticas de recompensas del usuario actual ---------- #
@router.get("/stats", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_reward_stats(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtiene estadísticas de recompensas del usuario actual.
    
    Devuelve:
    - Total de recompensas disponibles
    - Total de recompensas obtenidas
    - Porcentaje de completitud
    - Puntos totales de recompensas obtenidas
    """
    user_oid = ObjectId(current_user.id)
    
    # Total de recompensas en el sistema
    total_rewards = await db[REWARDS_COLLECTION].count_documents({})
    
    # Recompensas obtenidas por el usuario
    obtained_rewards = await db[REWARDS_COLLECTION].find({
        "users_awarded": user_oid
    }).to_list(length=None)
    
    obtained_count = len(obtained_rewards)
    
    # Puntos totales de recompensas obtenidas
    total_reward_points = sum(r.get("xp_bonus", 0) for r in obtained_rewards)
    
    # Porcentaje de completitud
    completion_percentage = (obtained_count / total_rewards * 100) if total_rewards > 0 else 0
    
    return {
        "total_rewards": total_rewards,
        "obtained_rewards": obtained_count,
        "remaining_rewards": total_rewards - obtained_count,
        "completion_percentage": round(completion_percentage, 2),
        "total_reward_points": total_reward_points
    }


# ========== CRUD DE RECOMPENSAS (SOLO PROFESORES) ==========
# Estas rutas son accesibles solo para profesores
# ---------- Rutas CRUD de recompensas ---------- #
@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_teacher_role)])
async def create_reward(
    reward_data: RewardCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Crea una nueva recompensa en el sistema.
    Solo accesible para profesores.
    """
    from services.rewards_crud import create_reward as create_reward_service
    
    # Agregar ID del profesor que crea la recompensa
    reward_dict = reward_data.model_dump()
    reward_dict["created_by"] = current_user.id
    
    created_reward = await create_reward_service(db, reward_dict)
    
    return {
        "message": "Recompensa creada exitosamente",
        "reward": created_reward
    }


@router.get("/all", status_code=status.HTTP_200_OK, dependencies=[Depends(require_teacher_role)])
async def get_all_rewards_for_management(
    is_active: bool = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtiene todas las recompensas para gestión.
    Solo accesible para profesores.
    Opcionalmente filtra por estado activo.
    """
    from services.rewards_crud import get_all_rewards
    
    rewards = await get_all_rewards(db, is_active)
    
    response = {
        "total": len(rewards),
        "rewards": rewards
    }
    
    print(f"✅ GET /all - Retornando {len(rewards)} recompensas enriquecidas")
    for reward in rewards:
        reward_type = reward.get('reward_type', 'FALTA reward_type')
        criteria = reward.get('criteria', {})
        print(f"   - {reward.get('title')}: type={reward_type}, lesson_title='{criteria.get('lesson_title')}', module_number={criteria.get('module_number')}")
    
    return response


@router.get("/{reward_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(require_teacher_role)])
async def get_reward_detail(
    reward_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtiene los detalles de una recompensa específica.
    Solo accesible para profesores.
    """
    from services.rewards_crud import get_reward_by_id
    
    reward = await get_reward_by_id(db, reward_id)
    
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recompensa no encontrada"
        )
    
    # Normalizar la recompensa
    reward = _normalize_reward(reward)
    
    return reward


@router.put("/{reward_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(require_teacher_role)])
async def update_reward_endpoint(
    reward_id: str,
    reward_data: RewardUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Actualiza una recompensa existente.
    Solo accesible para profesores.
    """
    from services.rewards_crud import update_reward
    
    # Filtrar campos None
    update_dict = {k: v for k, v in reward_data.model_dump().items() if v is not None}
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron campos para actualizar"
        )
    
    updated_reward = await update_reward(db, reward_id, update_dict)
    
    if not updated_reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recompensa no encontrada"
        )
    
    return {
        "message": "Recompensa actualizada exitosamente",
        "reward": updated_reward
    }


@router.delete("/{reward_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(require_teacher_role)])
async def delete_reward_endpoint(
    reward_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Elimina una recompensa del sistema.
    Solo accesible para profesores.
    """
    from services.rewards_crud import delete_reward
    
    success = await delete_reward(db, reward_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recompensa no encontrada"
        )
    
    return {
        "message": "Recompensa eliminada exitosamente"
    }

# ---------- Toggle de estado activo/inactivo de recompensa ---------- #
@router.patch("/{reward_id}/toggle", status_code=status.HTTP_200_OK, dependencies=[Depends(require_teacher_role)])
async def toggle_reward_status_endpoint(
    reward_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Activa o desactiva una recompensa (toggle).
    Solo accesible para profesores.
    """
    from services.rewards_crud import toggle_reward_status
    
    updated_reward = await toggle_reward_status(db, reward_id)
    
    if not updated_reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recompensa no encontrada"
        )
    
    status_text = "activada" if updated_reward["is_active"] else "desactivada"
    
    return {
        "message": f"Recompensa {status_text} exitosamente",
        "reward": updated_reward
    }

# ---------- Otorgar recompensa a un usuario específico ---------- #
@router.patch("/{reward_id}/award-user", status_code=status.HTTP_200_OK, dependencies=[Depends(require_teacher_role)])
async def award_reward_to_user(
    reward_id: str,
    request_data: dict,  # {"user_id": "..."}
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Otorga una recompensa manualmente a un usuario específico.
    Solo accesible para profesores.
    
    Body:
    {
      "user_id": "507f1f77bcf86cd799439011"
    }
    """
    from bson import ObjectId
    
    user_id = request_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere user_id en el body"
        )
    
    # Validar ObjectId
    if not ObjectId.is_valid(reward_id) or not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    reward_oid = ObjectId(reward_id)
    user_oid = ObjectId(user_id)
    
    # Obtener la recompensa
    reward = await db[REWARDS_COLLECTION].find_one({"_id": reward_oid})
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recompensa no encontrada"
        )
    
    # Verificar que el usuario no ya tiene la recompensa
    if user_oid in reward.get("users_awarded", []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este usuario ya tiene esta recompensa"
        )
    
    # Otorgar: sumar XP bonus al usuario
    xp_bonus = reward.get("xp_bonus", 0)
    await db["users"].update_one(
        {"_id": user_oid},
        {"$inc": {"total_points": xp_bonus}}
    )
    
    # Registrar en historial de XP
    from services.xp_history import XPHistoryService
    await XPHistoryService.record_xp(
        db,
        user_id=user_id,
        amount=xp_bonus,
        reason="reward_awarded",
        reward_id=reward_id,
        metadata={
            "reward_title": reward.get("title", ""),
            "reward_type": reward.get("reward_type", "custom"),
            "xp_bonus": xp_bonus
        }
    )
    
    # Agregar usuario a users_awarded
    await db[REWARDS_COLLECTION].update_one(
        {"_id": reward_oid},
        {"$push": {"users_awarded": user_oid}}
    )
    
    return {
        "message": f"Recompensa '{reward['title']}' otorgada exitosamente a usuario",
        "xp_awarded": xp_bonus,
        "reward_title": reward["title"]
    }
