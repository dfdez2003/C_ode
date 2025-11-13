from motor.motor_asyncio import AsyncIOMotorClient
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
exercises_collection = db["exercises"]
lessons_collection = db["lessons"]
modules_collection = db["modules"]
rewards_collection = db["rewards"]
sessions_collection = db["sessions"]
userprogress_collection = db["user_progress"]
userrewards_collection = db["user_rewards"]
client = mongo_client  # Exporta el cliente por si necesitas start_session()

