from schemas.users import UserCreate, UserResponse, UserStreak
from typing import Optional
from db.db import users_collection
from datetime import datetime
from passlib.context import CryptContext
from fastapi import HTTPException, status
from utils.user import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def get_user_by_username(username: str) -> Optional[dict]:
    return await users_collection.find_one({"username": username})

async def get_user_by_email(email: str) -> Optional[dict]:
    return await users_collection.find_one({"email": email})


async def register_user_service(user_data: UserCreate) -> UserResponse:
    if await get_user_by_email(user_data.email):
        raise ValueError("Email already registered")
    if await get_user_by_username(user_data.username):
        raise ValueError("Username already taken")
    
    user_dic = user_data.model_dump()  # Convertir a diccionario# este user data es el que me llega del front
    user_dic["password_hash"] = get_password_hash(user_dic.pop("password")) # Hashear la contraseña
    user_dic["role"] = "student"  # Asignar rol por defecto
    user_dic["created_at"] = datetime.utcnow()  # Fecha de creación
    user_dic["streak"] = UserStreak().model_dump()  # Racha inicial
    user_dic["total_points"] = 0  # Puntos iniciales
    user_dic["last_session_id"] = None  # Última sesión inicial

    result = await users_collection.insert_one(user_dic)  # Insertar en la base de datos
    # user_dic["id"] = str(result.inserted_id)  # Convertir ObjectId a string  
    user_dic["id"] = str(result.inserted_id)
    return UserResponse.model_validate(user_dic)  # Retornar con el schema de salida

async def authentificate_user_service(username: str, password: str) -> Optional[UserResponse]:
    user_dic = await get_user_by_username(username)
    if not user_dic:
        return None
    if not verify_password(password, user_dic.get("password_hash")):
        return None
    user_dic["id"] = str(user_dic["_id"])  # Convertir ObjectId a string
    return UserResponse.model_validate(user_dic)

# Servicio para obtener el usuario actual desde el token
async def get_current_user_service(token_data: TokenData) -> UserResponse:
    user = await get_user_by_username(token_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user["id"] = str(user["_id"])  # Convertir ObjectId a string
    return UserResponse.model_validate(user)



# services/user.py

# ... (código anterior)

async def register_teacher_service(user_data: UserCreate) -> UserResponse:
    if await get_user_by_email(user_data.email):
        raise ValueError("El correo ya está registrado.")
    if await get_user_by_username(user_data.username):
        raise ValueError("El nombre de usuario ya está en uso.")

    user_dict = user_data.model_dump()
    user_dict["password_hash"] = get_password_hash(user_dict.pop("password"))
    user_dict["role"] = "teacher"  # Asigna el rol "teacher"
    user_dict["created_at"] = datetime.utcnow()

    # Los campos específicos de estudiante se pueden omitir o establecer en valores por defecto
    user_dict["streak"] = UserStreak().model_dump()
    user_dict["total_points"] = 0
    user_dict["last_session_id"] = None
    
    result = await users_collection.insert_one(user_dict)
    
    user_dict["_id"] = result.inserted_id
    user_dict["id"] = str(user_dict["_id"])  # Convertir ObjectId a string

    return UserResponse.model_validate(user_dict)