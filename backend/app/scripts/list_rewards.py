"""
Script para listar todas las recompensas y ver sus valores.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://FdezCompas:Fdez2003@cluster1.389ur.mongodb.net/")
MONGO_DB = "code"

async def list_rewards():
    """Lista todas las recompensas."""
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    
    print("📋 Listando todas las recompensas:\n")
    
    rewards = await db["rewards"].find().to_list(None)
    
    for reward in rewards:
        print(f"{'='*60}")
        print(f"ID: {reward['_id']}")
        print(f"Título: {reward['title']}")
        print(f"Tipo: {reward['reward_type']}")
        print(f"XP Bonus: {reward.get('xp_bonus', 'NO TIENE')}")
        print(f"Criterios: {reward.get('criteria', {})}")
        print(f"Activa: {reward.get('is_active', True)}")
        print(f"Usuarios Otorgados: {len(reward.get('users_awarded', []))} usuarios")
    
    print(f"\n{'='*60}")
    print(f"Total de recompensas: {len(rewards)}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(list_rewards())
