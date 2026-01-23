from schemas.users import UserCreate, UserResponse, UserStreak, TeacherCreate
from typing import Optional, List
from db.db import users_collection, sessions_collection
from datetime import datetime
from passlib.context import CryptContext
from fastapi import HTTPException, status
from utils.user import TokenData
from bson import ObjectId
from datetime import date, timedelta
import os


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Clave secreta para registro de profesores (debe estar en variables de entorno)
TEACHER_SECRET_KEY = os.getenv("TEACHER_SECRET_KEY", "default_secret_key_change_in_production")

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


async def register_teacher_service(user_data: TeacherCreate) -> UserResponse:
    """
    Registra un profesor con validación de clave secreta.
    La clave secreta se valida contra TEACHER_SECRET_KEY del entorno.
    """
    # Validar clave secreta
    if user_data.secret_key != TEACHER_SECRET_KEY:
        raise ValueError("Clave secreta incorrecta. No autorizado para crear cuenta de profesor.")
    
    if await get_user_by_email(user_data.email):
        raise ValueError("El correo ya está registrado.")
    if await get_user_by_username(user_data.username):
        raise ValueError("El nombre de usuario ya está en uso.")

    user_dict = user_data.model_dump(exclude={"secret_key"})  # Excluir secret_key del documento
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


async def list_all_users_service(role: Optional[str] = None) -> List[UserResponse]:
    """
    Lista todos los usuarios del sistema.
    Si se proporciona 'role', filtra por ese rol (student/teacher).
    """
    query = {}
    if role:
        query["role"] = role
    
    users_cursor = users_collection.find(query)
    users = await users_cursor.to_list(length=None)
    
    result = []
    for user in users:
        user["id"] = str(user["_id"])
        result.append(UserResponse.model_validate(user))
    
    return result


async def get_user_by_id_service(user_id: str) -> UserResponse:
    """
    Obtiene un usuario específico por su ID con toda su información.
    """
    try:
        user_obj_id = ObjectId(user_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de ID inválido")
    
    user = await users_collection.find_one({"_id": user_obj_id})
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    user["id"] = str(user["_id"])
    return UserResponse.model_validate(user)


async def update_user_streak(user_id: str, session_id: str) -> bool:
    """
    Actualiza el contador de racha (streak) y la fecha de última práctica
    basándose en el inicio de la sesión actual.
    """
    try:
        user_obj_id = ObjectId(user_id)
        session_obj_id = ObjectId(session_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format.")

    # 1. Obtener datos cruciales
    user_doc = await users_collection.find_one({"_id": user_obj_id})
    session_doc = await sessions_collection.find_one({"_id": session_obj_id})

    if not user_doc or not session_doc:
        return False # Usuario o sesión no encontrados

    # Extraer la fecha de inicio de la sesión (solo la parte de fecha)
    session_start_date: date = session_doc["start_time"].date()
    
    # Obtener la racha y la última fecha de práctica del usuario
    streak_data = user_doc.get("streak", {})
    last_practice_date: Optional[date] = streak_data.get("last_practice_date")
    current_days: int = streak_data.get("current_days", 0)

    new_days = current_days
    
    # 2. Convertir la última fecha de práctica a objeto date si existe
    if last_practice_date:
        # Si viene como datetime, lo convertimos a date para la comparación
        if isinstance(last_practice_date, datetime):
            last_practice_date = last_practice_date.date()
    
    # --- Lógica de la Racha ---
    
    if last_practice_date is None:
        # Caso 1: Primera práctica de la historia (Racha = 1)
        new_days = 1
        
    elif session_start_date > last_practice_date:
        # Caso 2: Se practica en un día posterior
        
        # Calcular el día inmediatamente posterior a la última práctica
        required_next_day = last_practice_date + timedelta(days=1)
        
        if session_start_date == required_next_day:
            # Caso 2a: Racha Continúa (practicó hoy, que es el día siguiente)
            new_days += 1
        else:
            # Caso 2b: Racha Rota (saltó un día o más, se reinicia)
            new_days = 1
            
    elif session_start_date == last_practice_date:
        # Caso 3: Ya practicó hoy, no incrementamos la racha, solo confirmamos la fecha.
        # No hacemos nada con new_days
        pass

    # 3. Actualizar la base de datos si hubo un cambio en la fecha de práctica
    if session_start_date != last_practice_date:
        await users_collection.update_one(
            {"_id": user_obj_id},
            {"$set": {
                "streak.current_days": new_days,
                "streak.last_practice_date": session_start_date # Se actualiza a la nueva fecha
            }}
        )
        return True
        
    return False