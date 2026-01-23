# backend/app/services/rewards_crud.py

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Dict, Any, Optional
from datetime import datetime

REWARDS_COLLECTION = "rewards"


def _convert_objectids_to_strings(doc: Dict[str, Any]) -> None:
    """
    Convierte recursivamente todos los ObjectIds a strings en un diccionario.
    Modifica el diccionario in-place.
    """
    for key, value in list(doc.items()):
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, dict):
            _convert_objectids_to_strings(value)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, ObjectId):
                    value[i] = str(item)
                elif isinstance(item, dict):
                    _convert_objectids_to_strings(item)


async def create_reward(db: AsyncIOMotorDatabase, reward_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea una nueva recompensa en la base de datos.
    
    Args:
        db: Conexión a MongoDB
        reward_data: Diccionario con los datos de la recompensa
            - title: str
            - description: str
            - icon: str
            - reward_type: str ('lesson_perfect', 'streak_milestone', 'xp_milestone', 'custom')
            - criteria: dict (opcional, según reward_type)
            - points: int (puntos que otorga)
            - created_by: str (user_id del profesor)
    
    Returns:
        Dict con la recompensa creada incluyendo _id
    """
    # Agregar timestamp de creación y campos iniciales
    reward_data['created_at'] = datetime.utcnow().isoformat()
    reward_data['updated_at'] = datetime.utcnow().isoformat()
    reward_data['is_active'] = reward_data.get('is_active', True)
    reward_data['users_awarded'] = reward_data.get('users_awarded', [])  # ✅ Campo para rastrear otorgamientos
    
    # Insertar en MongoDB
    result = await db[REWARDS_COLLECTION].insert_one(reward_data)
    
    # Obtener el documento insertado
    created_reward = await db[REWARDS_COLLECTION].find_one({"_id": result.inserted_id})
    
    # Convertir todos los ObjectIds a strings
    _convert_objectids_to_strings(created_reward)
    
    return created_reward




async def _enrich_reward_criteria(db: AsyncIOMotorDatabase, reward: Dict[str, Any]) -> None:
    """
    Enriquece los criterios de una recompensa con nombres legibles.
    Para "lesson_perfect": agrega lesson_title y module_number
    Para otros tipos: no hace nada
    Modifica el diccionario in-place.
    """
    if reward.get("reward_type") != "lesson_perfect":
        return
    
    criteria = reward.get("criteria", {})
    lesson_id = criteria.get("lesson_id")
    
    if not lesson_id:
        return
    
    # Convertir lesson_id a string para comparación
    lesson_id_str = str(lesson_id) if isinstance(lesson_id, str) else str(lesson_id)
    
    # Buscar la lección en todos los módulos
    modules = await db["modules"].find().to_list(length=None)
    
    for module in modules:
        module_number = module.get("order", "?")
        lessons = module.get("lessons", [])
        
        for lesson in lessons:
            lesson_obj_id = lesson.get("_id")
            # Comparar como strings para evitar problemas de tipo
            if str(lesson_obj_id) == lesson_id_str:
                # Encontramos la lección, enriquecer criteria
                criteria["lesson_title"] = lesson.get("title", "Lección desconocida")
                criteria["module_number"] = module_number
                # Reward enriched with lesson details
                return
    
    # Si no encuentra, avisar
    print(f"⚠️ No encontrada lección con ID: {lesson_id_str} para recompensa: {reward.get('title')}")


async def get_all_rewards(db: AsyncIOMotorDatabase, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
    """
    Obtiene todas las recompensas, opcionalmente filtradas por estado activo.
    Enriquece los criterios con nombres legibles (ej: lesson_title, module_number).
    
    Args:
        db: Conexión a MongoDB
        is_active: Si se especifica, filtra por estado activo/inactivo
    
    Returns:
        Lista de recompensas
    """
    query = {}
    if is_active is not None:
        query['is_active'] = is_active
    
    cursor = db[REWARDS_COLLECTION].find(query).sort("created_at", -1)
    rewards = await cursor.to_list(length=None)
    
    # Convertir todos los ObjectIds a strings y enriquecer criterios
    for reward in rewards:
        # Asegurar que todas las recompensas tengan is_active (compatibilidad con recompensas antiguas)
        if 'is_active' not in reward:
            reward['is_active'] = True
        
        # Enriquecer criterios con nombres
        await _enrich_reward_criteria(db, reward)
        
        _convert_objectids_to_strings(reward)
    
    return rewards


async def get_reward_by_id(db: AsyncIOMotorDatabase, reward_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene una recompensa específica por su ID.
    
    Args:
        db: Conexión a MongoDB
        reward_id: ID de la recompensa
    
    Returns:
        Diccionario con la recompensa o None si no existe
    """
    if not ObjectId.is_valid(reward_id):
        return None
    
    reward = await db[REWARDS_COLLECTION].find_one({"_id": ObjectId(reward_id)})
    
    if reward:
        # Asegurar que tenga is_active (compatibilidad con recompensas antiguas)
        if 'is_active' not in reward:
            reward['is_active'] = True
        _convert_objectids_to_strings(reward)
    
    return reward


async def update_reward(db: AsyncIOMotorDatabase, reward_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Actualiza una recompensa existente.
    
    Args:
        db: Conexión a MongoDB
        reward_id: ID de la recompensa a actualizar
        update_data: Diccionario con los campos a actualizar
    
    Returns:
        Recompensa actualizada o None si no existe
    """
    if not ObjectId.is_valid(reward_id):
        return None
    
    # Agregar timestamp de actualización
    update_data['updated_at'] = datetime.utcnow().isoformat()
    
    # Eliminar campos que no deben actualizarse
    update_data.pop('_id', None)
    update_data.pop('created_at', None)
    update_data.pop('created_by', None)
    
    result = await db[REWARDS_COLLECTION].find_one_and_update(
        {"_id": ObjectId(reward_id)},
        {"$set": update_data},
        return_document=True
    )
    
    if result:
        _convert_objectids_to_strings(result)
    
    return result


async def delete_reward(db: AsyncIOMotorDatabase, reward_id: str) -> bool:
    """
    Elimina una recompensa de la base de datos.
    
    Args:
        db: Conexión a MongoDB
        reward_id: ID de la recompensa a eliminar
    
    Returns:
        True si se eliminó, False si no existe
    """
    if not ObjectId.is_valid(reward_id):
        return False
    
    result = await db[REWARDS_COLLECTION].delete_one({"_id": ObjectId(reward_id)})
    return result.deleted_count > 0


async def toggle_reward_status(db: AsyncIOMotorDatabase, reward_id: str) -> Optional[Dict[str, Any]]:
    """
    Activa o desactiva una recompensa (toggle del campo is_active).
    
    Args:
        db: Conexión a MongoDB
        reward_id: ID de la recompensa
    
    Returns:
        Recompensa actualizada o None si no existe
    """
    if not ObjectId.is_valid(reward_id):
        return None
    
    # Obtener estado actual
    reward = await db[REWARDS_COLLECTION].find_one({"_id": ObjectId(reward_id)})
    if not reward:
        return None
    
    # Invertir el estado
    new_status = not reward.get('is_active', True)
    
    result = await db[REWARDS_COLLECTION].find_one_and_update(
        {"_id": ObjectId(reward_id)},
        {
            "$set": {
                "is_active": new_status,
                "updated_at": datetime.utcnow().isoformat()
            }
        },
        return_document=True
    )
    
    if result:
        _convert_objectids_to_strings(result)
    
    return result


async def get_rewards_by_type(db: AsyncIOMotorDatabase, reward_type: str) -> List[Dict[str, Any]]:
    """
    Obtiene todas las recompensas de un tipo específico.
    
    Args:
        db: Conexión a MongoDB
        reward_type: Tipo de recompensa ('lesson_perfect', 'streak_milestone', etc.)
    
    Returns:
        Lista de recompensas del tipo especificado
    """
    cursor = db[REWARDS_COLLECTION].find({
        "reward_type": reward_type,
        "is_active": True
    }).sort("created_at", -1)
    
    rewards = await cursor.to_list(length=None)
    
    for reward in rewards:
        if 'is_active' not in reward:
            reward['is_active'] = True
        _convert_objectids_to_strings(reward)
    
    return rewards
