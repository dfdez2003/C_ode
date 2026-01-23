"""
Script para cargar recompensas iniciales en la base de datos.
Ejecutar: python -m app.scripts.seed_rewards

"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
import sys

# Configuración
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "code_learning_platform"
REWARDS_COLLECTION = "rewards"

# ==================== RECOMPENSAS INICIALES ====================

INITIAL_REWARDS = [
    # ============ LECCIONES PERFECTAS ============
    {
        "title": "🎯 Perfección en Arrays",
        "description": "Completaste la lección de Arrays con 100% de puntuación",
        "icon": "🎯",
        "reward_type": "lesson_perfect",
        "criteria": {
            "lesson_id": "arrays_lesson_id"  # Se debe reemplazar con ID real
        },
        "points": 25,
        "is_active": True,
        "users_awarded": [],
        "created_by": "sistema",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "title": "🎯 Perfección en Punteros",
        "description": "Completaste la lección de Punteros con 100% de puntuación",
        "icon": "🎯",
        "reward_type": "lesson_perfect",
        "criteria": {
            "lesson_id": "punteros_lesson_id"  # Se debe reemplazar con ID real
        },
        "points": 30,
        "is_active": True,
        "users_awarded": [],
        "created_by": "sistema",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    
    # ============ HITOS DE RACHA ============
    {
        "title": "🔥 3 Días Consecutivos",
        "description": "Completaste 3 días consecutivos de práctica",
        "icon": "🔥",
        "reward_type": "streak_milestone",
        "criteria": {
            "streak": 3
        },
        "points": 20,
        "is_active": True,
        "users_awarded": [],
        "created_by": "sistema",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "title": "🔥 7 Días Consecutivos",
        "description": "¡Impresionante! 7 días consecutivos de práctica",
        "icon": "🔥",
        "reward_type": "streak_milestone",
        "criteria": {
            "streak": 7
        },
        "points": 50,
        "is_active": True,
        "users_awarded": [],
        "created_by": "sistema",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "title": "🔥 30 Días Consecutivos",
        "description": "¡Legendario! 30 días de racha sin parar",
        "icon": "🔥",
        "reward_type": "streak_milestone",
        "criteria": {
            "streak": 30
        },
        "points": 150,
        "is_active": True,
        "users_awarded": [],
        "created_by": "sistema",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    
    # ============ HITOS DE XP ============
    {
        "title": "⭐ Primer Paso",
        "description": "Ganaste tus primeros 100 XP",
        "icon": "⭐",
        "reward_type": "xp_milestone",
        "criteria": {
            "xp_threshold": 100
        },
        "points": 10,
        "is_active": True,
        "users_awarded": [],
        "created_by": "sistema",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "title": "✨ Nivel Aprendiz",
        "description": "Alcanzaste 500 XP - ¡Buen trabajo!",
        "icon": "✨",
        "reward_type": "xp_milestone",
        "criteria": {
            "xp_threshold": 500
        },
        "points": 30,
        "is_active": True,
        "users_awarded": [],
        "created_by": "sistema",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "title": "💎 Nivel Experto",
        "description": "¡Impresionante! Alcanzaste 1000 XP",
        "icon": "💎",
        "reward_type": "xp_milestone",
        "criteria": {
            "xp_threshold": 1000
        },
        "points": 60,
        "is_active": True,
        "users_awarded": [],
        "created_by": "sistema",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "title": "👑 Maestro del Código",
        "description": "¡Legendario! Alcanzaste 2000 XP",
        "icon": "👑",
        "reward_type": "xp_milestone",
        "criteria": {
            "xp_threshold": 2000
        },
        "points": 100,
        "is_active": True,
        "users_awarded": [],
        "created_by": "sistema",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    
    # ============ RECOMPENSAS PERSONALIZADAS ============
    {
        "title": "🏆 Campeón del Bootcamp",
        "description": "Recompensa especial para los mejores estudiantes",
        "icon": "🏆",
        "reward_type": "custom",
        "criteria": {},
        "points": 200,
        "is_active": False,  # Desactivada hasta que se otorgue manualmente
        "users_awarded": [],
        "created_by": "sistema",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "title": "🎓 Graduación",
        "description": "Completaste todos los módulos y lecciones",
        "icon": "🎓",
        "reward_type": "custom",
        "criteria": {},
        "points": 300,
        "is_active": False,  # Se otorgará cuando terminen el curso
        "users_awarded": [],
        "created_by": "sistema",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
]


async def seed_rewards():
    """Inserta las recompensas iniciales en MongoDB"""
    
    print("🔗 Conectando a MongoDB en:", MONGODB_URL)
    client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    
    try:
        # Verificar conexión
        await client.admin.command('ping')
        print("Conexión a MongoDB establecida\n")
        
        db = client[DATABASE_NAME]
        
        # Verificar si las recompensas ya existen
        existing_count = await db[REWARDS_COLLECTION].count_documents({})
        
        if existing_count > 0:
            print(f"Ya existen {existing_count} recompensas en la BD.")
            print("Continuando con la inserción de nuevas recompensas...\n")
        
        # Insertar recompensas
        result = await db[REWARDS_COLLECTION].insert_many(INITIAL_REWARDS)
        
        print(f"Se insertaron {len(result.inserted_ids)} recompensas iniciales\n")
        print("Recompensas insertadas:")
        for i, reward in enumerate(INITIAL_REWARDS, 1):
            status = "🟢" if reward['is_active'] else "⚪"
            print(f"  {status} {i}. {reward['title']} ({reward['reward_type']}) - {reward['points']} pts")
        
        print("\n" + "="*70)
        print("⚠️  IMPORTANTE:")
        print("="*70)
        print("1. Actualiza los lesson_id en las recompensas de lecciones perfectas")
        print("   con los IDs reales de tus lecciones en MongoDB.")
        print("")
        print("2. Ejecuta esta consulta en MongoDB para obtener los lesson_id reales:")
        print("   db.lessons.find({}, {_id: 1, title: 1})")
        print("")
        print("3. Luego actualiza manualmente o modifica el seed_rewards.py con los IDs correctos")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Soluciones posibles:")
        print("   1. Asegúrate de que MongoDB está corriendo:")
        print("      - Linux/Mac: mongod")
        print("      - Docker: docker run -d -p 27017:27017 mongo")
        print("   2. Verifica que MONGODB_URL es correcto (actual: {})".format(MONGODB_URL))
        print("   3. Comprueba que la BD y colecciones existen")
        sys.exit(1)
    finally:
        client.close()
        print("\n🔌 Conexión cerrada")


if __name__ == "__main__":
    asyncio.run(seed_rewards())

