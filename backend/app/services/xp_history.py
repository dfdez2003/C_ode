"""
Servicio para registrar el historial de XP de los usuarios.
Permite auditoría completa de dónde viene cada punto de XP.
"""

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone
from typing import List, Dict, Any

XP_HISTORY_COLLECTION = "xp_history"
USERS_COLLECTION = "users"

class XPHistoryService:
    
    @staticmethod
    async def record_xp(
        db: AsyncIOMotorDatabase,
        user_id: str,
        amount: int,
        reason: str,
        reward_id: str = None,
        lesson_id: str = None,
        module_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Registra una transacción de XP en el historial.
        
        Args:
            user_id: ID del usuario
            amount: Cantidad de XP (puede ser positivo o negativo)
            reason: Razón del XP (ej: "lesson_completion", "perfection_bonus", "reward_awarded", etc)
            reward_id: ID de la recompensa (si aplica)
            lesson_id: ID de la lección (si aplica)
            module_id: ID del módulo (si aplica)
            metadata: Datos adicionales para más contexto
        
        Returns:
            Documento insertado
        """
        
        history_doc = {
            "user_id": user_id,
            "amount": amount,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc),
            "reward_id": ObjectId(reward_id) if reward_id and ObjectId.is_valid(reward_id) else None,
            "lesson_id": lesson_id,
            "module_id": module_id,
            "metadata": metadata or {}
        }
        
        result = await db[XP_HISTORY_COLLECTION].insert_one(history_doc)
        
        history_doc["_id"] = result.inserted_id
        return history_doc
    
    @staticmethod
    async def get_user_xp_history(
        db: AsyncIOMotorDatabase,
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de XP de un usuario.
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de registros
            skip: Número de registros a saltar (para paginación)
        
        Returns:
            Lista de transacciones de XP
        """
        
        cursor = db[XP_HISTORY_COLLECTION].find(
            {"user_id": user_id}
        ).sort("timestamp", -1).skip(skip).limit(limit)
        
        history = []
        async for doc in cursor:
            history.append(_format_history_doc(doc))
        
        return history
    
    @staticmethod
    async def get_xp_summary(
        db: AsyncIOMotorDatabase,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Obtiene un resumen del XP del usuario.
        
        Returns:
            {
                "total_xp": int,
                "total_transactions": int,
                "breakdown_by_reason": {
                    "reason": count
                }
            }
        """
        
        # Obtener total de transacciones
        total_transactions = await db[XP_HISTORY_COLLECTION].count_documents(
            {"user_id": user_id}
        )
        
        # Obtener suma de XP
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": None,
                    "total_xp": {"$sum": "$amount"},
                    "by_reason": {
                        "$push": {
                            "reason": "$reason",
                            "amount": "$amount"
                        }
                    }
                }
            }
        ]
        
        result = await db[XP_HISTORY_COLLECTION].aggregate(pipeline).to_list(1)
        
        if not result:
            return {
                "total_xp": 0,
                "total_transactions": 0,
                "breakdown_by_reason": {}
            }
        
        # Contar por razón
        breakdown = {}
        for item in result[0]["by_reason"]:
            reason = item["reason"]
            if reason not in breakdown:
                breakdown[reason] = 0
            breakdown[reason] += 1
        
        return {
            "total_xp": result[0]["total_xp"],
            "total_transactions": total_transactions,
            "breakdown_by_reason": breakdown
        }


def _format_history_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Formatea un documento de historial para el frontend."""
    return {
        "id": str(doc["_id"]),
        "user_id": doc["user_id"],
        "amount": doc["amount"],
        "reason": doc["reason"],
        "timestamp": doc["timestamp"].isoformat() if isinstance(doc["timestamp"], datetime) else doc["timestamp"],
        "reward_id": str(doc.get("reward_id")) if doc.get("reward_id") else None,
        "lesson_id": doc.get("lesson_id"),
        "module_id": doc.get("module_id"),
        "metadata": doc.get("metadata", {})
    }
