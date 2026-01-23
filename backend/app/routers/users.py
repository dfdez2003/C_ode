from fastapi import APIRouter, HTTPException, status, Depends, Query
from schemas.users import UserResponse, UserCreate, UserLogin, Token, TeacherCreate
from db.db import users_collection
from utils.user import create_access_token, get_current_user_from_token
from services.users import (
    register_user_service, 
    authentificate_user_service, 
    get_current_user_service, 
    register_teacher_service,
    list_all_users_service,
    get_user_by_id_service
)
from datetime import datetime
from typing import Dict, Any, Optional, List
from bson import ObjectId
from db.db import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase


# Router de usuarios
router = APIRouter(prefix="/users",tags=["users"],)

# ---------------------------> Rutas para la gestión de usuarios <---------------------------

# POST -> Registro de usuario
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,summary=" Register new user")
async def register_user_route(user: UserCreate):
    try:
        new_user = await register_user_service(user)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# POST -> Login de usuario 
@router.post("/login", response_model= Token, summary=" Log in an existing user and reurn a JWT token")
async def login_user_route(form_data: UserLogin):
    """ Authenticates a user and return JWT token """
    # Mandamos a llamar el servicio que valida el usuario y lo retorna
    user = await authentificate_user_service(form_data.username, form_data.password)
    
    if not user: 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password", headers={"WWW-Authenticate": "Bearer"})
    
    # Crear el token JWT con username como sub e id adicional
    access_token = create_access_token(data={"sub": user.username, "id": user.id, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}
    
# GET -> Obtener el usuario actual autenticado
@router.get("/me", response_model=UserResponse, summary=" Get the current autenticated user")
async def read_current_user(token_data:Dict[str,Any] = Depends(get_current_user_from_token)):
    """ Retrieves the details of the current authenticated user """
    current_user = await get_current_user_service(token_data)
    return current_user

# POST -> Registro de profesor con clave secreta
@router.post("/register_teacher",response_model=UserResponse,status_code=status.HTTP_201_CREATED, summary="Registers a new user with 'teacher' role (requires secret key).")
async def register_teacher_route(user: TeacherCreate):
    """
    Registra un nuevo usuario con rol 'teacher'.
    Requiere una clave secreta válida (TEACHER_SECRET_KEY) para completar el registro.
    """
    try:
        new_user = await register_teacher_service(user)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

# GET -> Listar todos los usuarios (con filtro opcional por rol)
@router.get("/", response_model=List[UserResponse], summary="List all users (optionally filter by role)")
async def list_users_route(
    role: Optional[str] = Query(None, description="Filter by role: 'student' or 'teacher'")
):
    """
    Lista todos los usuarios del sistema.
    Opcionalmente filtra por rol usando el query parameter ?role=student o ?role=teacher
    """
    users = await list_all_users_service(role=role)
    return users


# GET -> Obtener un usuario específico por ID
@router.get("/{user_id}", response_model=UserResponse, summary="Get a specific user by ID")
async def get_user_by_id_route(user_id: str):
    """
    Obtiene la información completa de un usuario específico por su ID.
    Incluye: puntos totales, racha, fecha de creación, etc.
    """
    user = await get_user_by_id_service(user_id)
    return user

# GET -> Obtener la racha actual de un usuario específico
@router.get("/user/{user_id}/streak")
async def get_user_streak(user_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    user = await db["users"].find_one({"_id": ObjectId(user_id)}, {"streak": 1})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {
        "current_streak": user.get("streak", {}).get("current_days", 0),
        "last_practice": user.get("streak", {}).get("last_practice_date")
    }