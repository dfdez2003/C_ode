from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
from typing import Optional


# conexion a mongo db para usar compas 
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://FdezCompas:Fdez2003@cluster1.389ur.mongodb.net/")
# Cliente de mongo asíncrono
mongo_client = AsyncIOMotorClient(MONGO_URI)
# base de datos 
db = mongo_client["code"]

# Iniciamos como None 
client: Optional[AsyncIOMotorClient] = None

# Exporta las colecciones para importarlas fácilmente
users_collection = db["users"]
modules_collection = db["modules"]
rewards_collection = db["rewards"]
sessions_collection = db["sessions"]
# NOTA: lesson_progress y xp_history se usan directamente como db["nombre"]
# en sus respectivos servicios sin estar exportadas aquí

client = mongo_client  # Exporta el cliente por si necesitas start_session()

# Esta función es la que FastAPI necesita para inyectar el objeto DB.
async def get_database() -> AsyncIOMotorDatabase:
    """
    Retorna el objeto de la base de datos asíncrona.
    """
    # En proyectos grandes, aqui se maneja la conexión/desconexión.
    # Aquí, simplemente cede el objeto 'db' que ya está conectado.
    return db