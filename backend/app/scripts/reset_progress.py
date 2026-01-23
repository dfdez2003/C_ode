"""
Script para limpiar datos de progreso/avances de la base de datos.
Mantiene: usuarios, módulos, lecciones, ejercicios.
Limpia: progreso, sesiones, recompensas otorgadas, XP acumulado.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

# URI de MongoDB (la misma que usa la aplicación)
MONGO_URI = "mongodb+srv://FdezCompas:Fdez2003@cluster1.389ur.mongodb.net/"
DATABASE_NAME = "code"


async def reset_progress():
    """Limpia todas las colecciones de progreso manteniendo la estructura base."""
    
    print(" Conectando a MongoDB...")
    client = AsyncIOMotorClient(MONGO_URI, server_api=ServerApi('1'))
    db = client.get_database(DATABASE_NAME)
    
    try:
        # Verificar conexión
        await client.admin.command('ping')
        print(" Conexión exitosa a MongoDB\n")
        
        # 1. Limpiar colección de progreso de lecciones
        print(" Limpiando lesson_progress...")
        result = await db.lesson_progress.delete_many({})
        print(f"   Eliminados: {result.deleted_count} documentos\n")
        
        # 2. Limpiar colección de sesiones
        print(" Limpiando sessions...")
        result = await db.sessions.delete_many({})
        print(f"   Eliminados: {result.deleted_count} documentos\n")
        
        # 3. Limpiar colección user_progress (si existe)
        print(" Limpiando user_progress...")
        result = await db.user_progress.delete_many({})
        print(f"   Eliminados: {result.deleted_count} documentos\n")
        
        # 4. Resetear XP y rachas de usuarios (mantener usuarios pero resetear stats)
        print(" Reseteando estadísticas de usuarios...")
        result = await db.users.update_many(
            {"role": "student"},  # Solo estudiantes
            {
                "$set": {
                    "total_points": 0,
                    "current_streak": 0,
                    "last_activity_date": None,
                    "longest_streak": 0
                }
            }
        )
        print(f"   Actualizados: {result.modified_count} estudiantes\n")
        
        # 5. Limpiar users_awarded de todas las recompensas
        print(" Limpiando recompensas otorgadas...")
        result = await db.rewards.update_many(
            {},
            {
                "$set": {
                    "users_awarded": []
                }
            }
        )
        print(f"   Actualizadas: {result.modified_count} recompensas\n")
        
        # 6. Mostrar resumen de lo que se mantiene
        print("=" * 60)
        print(" RESUMEN - Colecciones mantenidas:")
        print("=" * 60)
        
        users_count = await db.users.count_documents({})
        teachers_count = await db.users.count_documents({"role": "teacher"})
        students_count = await db.users.count_documents({"role": "student"})
        print(f"👥 Usuarios totales: {users_count}")
        print(f"   - Profesores: {teachers_count}")
        print(f"   - Estudiantes: {students_count}")
        
        modules_count = await db.modules.count_documents({})
        print(f" Módulos: {modules_count}")
        
        rewards_count = await db.rewards.count_documents({})
        print(f" Recompensas (sin otorgar): {rewards_count}")
        
        print("\n" + "=" * 60)
        print(" LIMPIEZA COMPLETADA")
        print("=" * 60)
        print("Los estudiantes pueden empezar desde cero con:")
        print("  - XP: 0")
        print("  - Racha: 0")
        print("  - Sin lecciones completadas")
        print("  - Sin recompensas obtenidas")
        print("\nEstructura base mantenida:")
        print("  ✓ Usuarios (credenciales intactas)")
        print("  ✓ Módulos y lecciones")
        print("  ✓ Ejercicios")
        print("  ✓ Recompensas (listas para otorgar)")
        
    except Exception as e:
        print(f" Error durante la limpieza: {e}")
        raise
    
    finally:
        client.close()
        print("\n Conexión cerrada")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  SCRIPT DE LIMPIEZA DE PROGRESO")
    print("=" * 60)
    print("\n  ADVERTENCIA: Este script eliminará:")
    print("   - Todo el progreso de lecciones")
    print("   - Todas las sesiones")
    print("   - XP y rachas acumulados")
    print("   - Recompensas otorgadas")
    print("\n Se mantendrán:")
    print("   - Usuarios y contraseñas")
    print("   - Módulos, lecciones y ejercicios")
    print("   - Estructura de recompensas")
    
    confirm = input("\n¿Continuar? (escriba 'SI' para confirmar): ")
    
    if confirm.strip().upper() == "SI":
        print("\n Iniciando limpieza...\n")
        asyncio.run(reset_progress())
    else:
        print("\n Operación cancelada")
