from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone
from typing import Optional, Dict
from services.progress import update_user_streak  
from services.xp_history import XPHistoryService  

# Colecciones
USERS_COLLECTION = "users"
REWARDS_COLLECTION = "rewards"
PROGRESS_COLLECTION = "user_progress"
MODULES_COLLECTION = "modules"

class RewardService:

    @staticmethod
    async def process_lesson_completion(db: AsyncIOMotorDatabase, user_id: str, lesson_id: str, module_id: str):
        """
        Calcula y otorga XP, bonos y recompensas al terminar una lección.
                
        Lógica:
        1. Obtiene el progreso de lesson_progress (current_score y total_possible)
        2. Calcula XP proporcional según puntos obtenidos vs totales posibles
        3. Si es perfecta (100% de puntos), da un bono extra del 15%
        4. Actualiza total_points del usuario
        5. Busca y otorga recompensas por "lección perfecta" si aplica
        """
        # 1. Obtener la lección del módulo para saber su xp_reward
        module = await db[MODULES_COLLECTION].find_one({"_id": ObjectId(module_id)})
        lesson = next((l for l in module["lessons"] if str(l["_id"]) == lesson_id), None)
        
        if not lesson:
            return None

        lesson_xp_reward = lesson.get("xp_reward", 0)

        # 2. Obtener el progreso de lesson_progress
        lesson_progress = await db["lesson_progress"].find_one({
            "user_id": user_id,
            "lesson_id": lesson_id
        })
        
        if not lesson_progress:
            return None
        
        # Obtener current_score y total_possible
        points_obtained = lesson_progress.get("current_score", 0)
        total_possible_points = lesson_progress.get("total_possible", 0)

        # 3. Cálculo de XP Proporcional
        # Formula: (puntos_obtenidos / total_posibles) * leccion_xp_reward
        earned_xp = 0
        if total_possible_points > 0:
            percentage = points_obtained / total_possible_points
            earned_xp = int(percentage * lesson_xp_reward)

        # 4. Bono por Perfección (Extra)
        perfection_bonus = 0
        is_perfect = (points_obtained == total_possible_points) and (total_possible_points > 0)
        if is_perfect:
            perfection_bonus = int(lesson_xp_reward * 0.15)  # 15% de bono por no fallar nada

        total_to_add = earned_xp + perfection_bonus

        # 5. Actualizar total_points del Usuario
        await db[USERS_COLLECTION].update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"total_points": total_to_add}}
        )
        
        # 5a. Registrar en historial de XP
        await XPHistoryService.record_xp(
            db,
            user_id=user_id,
            amount=earned_xp,
            reason="lesson_completion",
            lesson_id=lesson_id,
            module_id=module_id,
            metadata={
                "lesson_title": lesson.get("title", ""),
                "points_obtained": points_obtained,
                "total_possible": total_possible_points,
                "percentage": round((points_obtained / total_possible_points * 100), 2) if total_possible_points > 0 else 0
            }
        )
        
        # 5b. Registrar bono de perfección si aplica
        if is_perfect:
            await XPHistoryService.record_xp(
                db,
                user_id=user_id,
                amount=perfection_bonus,
                reason="perfection_bonus",
                lesson_id=lesson_id,
                module_id=module_id,
                metadata={
                    "lesson_title": lesson.get("title", ""),
                    "bonus_percentage": "15%"
                }
            )

        # 6. Buscar y otorgar recompensas por "lección perfecta" si aplica
        perfect_lesson_rewards = []
        if is_perfect:
            user_oid = ObjectId(user_id)
            # ✅ NUEVA ESTRUCTURA: Buscar recompensas tipo "lesson_perfect" con criteria.lesson_id
            cursor = db[REWARDS_COLLECTION].find({
                "reward_type": "lesson_perfect",
                "criteria.lesson_id": lesson_id,
                "is_active": True,
                "users_awarded": {"$ne": user_oid}
            })
            
            async for reward in cursor:
                # Obtener XP bonus de la recompensa (cambiar "points" a "xp_bonus")
                xp_bonus = reward.get("xp_bonus", 0)
                await db[USERS_COLLECTION].update_one(
                    {"_id": user_oid},
                    {"$inc": {"total_points": xp_bonus}}
                )
                
                # Registrar en historial
                await XPHistoryService.record_xp(
                    db,
                    user_id=user_id,
                    amount=xp_bonus,
                    reason="reward_awarded",
                    reward_id=str(reward["_id"]),
                    lesson_id=lesson_id,
                    module_id=module_id,
                    metadata={
                        "reward_title": reward.get("title", ""),
                        "reward_type": "lesson_perfect"
                    }
                )
                
                # Marcar como entregada
                await db[REWARDS_COLLECTION].update_one(
                    {"_id": reward["_id"]},
                    {"$push": {"users_awarded": user_oid}}
                )
                perfect_lesson_rewards.append(reward["title"])
                total_to_add += xp_bonus

        # 7. Retornar resumen para el frontend
        return {
            "total_xp_earned": total_to_add,      # Total XP ganado (earned + bonus + rewards)
            "lesson_xp": earned_xp,               # XP base de la lección
            "bonus_xp": perfection_bonus,         # Bono por perfección
            "is_perfect": is_perfect,
            "perfect_lesson_achievements": perfect_lesson_rewards
        }

    @staticmethod
    async def handle_streak_and_achievements(db: AsyncIOMotorDatabase, user_id: str, reference_time: datetime):
        """
        Actualiza racha usando el tiempo de la sesión y otorga recompensas.
        """        
        # 1. Actualizamos la racha formalmente en la base de datos
        # Esta función ya maneja si es día consecutivo, reset o mismo día.
        new_streak_value = await update_user_streak(db, user_id, reference_time)
        
        # 2. Ahora buscamos si hay recompensas para esta nueva racha
        user_oid = ObjectId(user_id)
        new_rewards_names = []
        
        # ✅ NUEVA ESTRUCTURA: Buscar recompensas tipo "streak_milestone" con criteria.streak
        cursor = db[REWARDS_COLLECTION].find({
            "reward_type": "streak_milestone",
            "criteria.streak": new_streak_value,
            "is_active": True,
            "users_awarded": {"$ne": user_oid}
        })
        
        async for reward in cursor:
            # Otorgamos el XP bonus del RewardModel al total del usuario
            xp_bonus = reward.get("xp_bonus", 0)
            await db[USERS_COLLECTION].update_one(
                {"_id": user_oid},
                {"$inc": {"total_points": xp_bonus}}
            )
            
            # Registrar en historial
            await XPHistoryService.record_xp(
                db,
                user_id=user_id,
                amount=xp_bonus,
                reason="reward_awarded",
                reward_id=str(reward["_id"]),
                metadata={
                    "reward_title": reward.get("title", ""),
                    "reward_type": "streak_milestone",
                    "streak_days": new_streak_value
                }
            )
            
            # Marcamos la recompensa como entregada para este usuario
            await db[REWARDS_COLLECTION].update_one(
                {"_id": reward["_id"]},
                {"$push": {"users_awarded": user_oid}}
            )
            new_rewards_names.append(reward["title"])
            
        return {
            "current_streak": new_streak_value,
            "new_achievements": new_rewards_names
        }

    @staticmethod
    async def process_xp_milestones(db: AsyncIOMotorDatabase, user_id: str, new_total_xp: int):
        """
        Otorga recompensas por hitos de XP.
        Se llama después de actualizar total_points del usuario.
        """
        user_oid = ObjectId(user_id)
        awarded_achievements = []
        
        # ✅ Buscar recompensas tipo "xp_milestone" donde criteria.xp_threshold <= new_total_xp
        cursor = db[REWARDS_COLLECTION].find({
            "reward_type": "xp_milestone",
            "is_active": True,
            "users_awarded": {"$ne": user_oid}
        })
        
        async for reward in cursor:
            threshold = reward.get("criteria", {}).get("xp_threshold")
            if threshold and new_total_xp >= threshold:
                # Obtener XP bonus
                xp_bonus = reward.get("xp_bonus", 0)
                
                # Otorgar XP bonus al usuario
                await db[USERS_COLLECTION].update_one(
                    {"_id": user_oid},
                    {"$inc": {"total_points": xp_bonus}}
                )
                
                # Registrar en historial
                await XPHistoryService.record_xp(
                    db,
                    user_id=user_id,
                    amount=xp_bonus,
                    reason="reward_awarded",
                    reward_id=str(reward["_id"]),
                    metadata={
                        "reward_title": reward.get("title", ""),
                        "reward_type": "xp_milestone",
                        "xp_threshold": threshold,
                        "user_total_xp": new_total_xp + xp_bonus
                    }
                )
                
                # Marcar como entregada
                await db[REWARDS_COLLECTION].update_one(
                    {"_id": reward["_id"]},
                    {"$push": {"users_awarded": user_oid}}
                )
                awarded_achievements.append(reward["title"])
        
        return awarded_achievements


# ==================== FUNCIONES CRUD DE RECOMPENSAS ====================

async def create_reward_service(db: AsyncIOMotorDatabase, reward_data: dict) -> dict:
    """
    Crea una nueva recompensa en el sistema.
    """
    # Preparar documento
    reward_doc = {
        "name": reward_data["name"],
        "description": reward_data["description"],
        "type": reward_data["type"],
        "points": reward_data["points"],
        "users_awarded": []  # Inicialmente vacío
    }
    
    # Agregar campos opcionales si existen
    if "required_streak" in reward_data and reward_data["required_streak"] is not None:
        reward_doc["required_streak"] = reward_data["required_streak"]
    
    if "required_lesson_id" in reward_data and reward_data["required_lesson_id"] is not None:
        reward_doc["required_lesson_id"] = reward_data["required_lesson_id"]
    
    if "required_module_id" in reward_data and reward_data["required_module_id"] is not None:
        reward_doc["required_module_id"] = reward_data["required_module_id"]
    
    # Insertar en la base de datos
    result = await db[REWARDS_COLLECTION].insert_one(reward_doc)
    
    # Obtener el documento insertado
    created_reward = await db[REWARDS_COLLECTION].find_one({"_id": result.inserted_id})
    created_reward["id"] = str(created_reward.pop("_id"))
    created_reward["users_awarded"] = [str(uid) for uid in created_reward.get("users_awarded", [])]
    
    return created_reward


async def update_reward_service(db: AsyncIOMotorDatabase, reward_id: str, update_data: dict) -> dict:
    """
    Actualiza una recompensa existente.
    Solo actualiza los campos que se proporcionen.
    """
    if not ObjectId.is_valid(reward_id):
        raise ValueError("ID de recompensa inválido")
    
    # Filtrar campos None (no actualizar lo que no se proporciona)
    update_fields = {k: v for k, v in update_data.items() if v is not None}
    
    if not update_fields:
        raise ValueError("No hay campos para actualizar")
    
    # Actualizar en la base de datos
    result = await db[REWARDS_COLLECTION].update_one(
        {"_id": ObjectId(reward_id)},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise ValueError("Recompensa no encontrada")
    
    # Obtener el documento actualizado
    updated_reward = await db[REWARDS_COLLECTION].find_one({"_id": ObjectId(reward_id)})
    updated_reward["id"] = str(updated_reward.pop("_id"))
    updated_reward["users_awarded"] = [str(uid) for uid in updated_reward.get("users_awarded", [])]
    
    return updated_reward


async def delete_reward_service(db: AsyncIOMotorDatabase, reward_id: str) -> bool:
    """
    Elimina una recompensa del sistema.
    """
    if not ObjectId.is_valid(reward_id):
        raise ValueError("ID de recompensa inválido")
    
    result = await db[REWARDS_COLLECTION].delete_one({"_id": ObjectId(reward_id)})
    
    if result.deleted_count == 0:
        raise ValueError("Recompensa no encontrada")
    
    return True