from fastapi import APIRouter, HTTPException, status, Depends
from schemas.users import UserResponse, UserCreate, UserLogin, Token
from db.db import users_collection
from utils.user import create_access_token, get_current_user_from_token
from services.users import register_user_service, authentificate_user_service, get_current_user_service, register_teacher_service
from datetime import datetime
from typing import Dict, Any

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
    
    # Crear el token JWT
    access_token = create_access_token(data={"sub": user.username,"role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}
    
# GET -> Obtener el usuario actual autenticado
@router.get("/me", response_model=UserResponse, summary=" Get the current autenticated user")
async def read_current_user(token_data:Dict[str,Any] = Depends(get_current_user_from_token)):
    """ Retrieves the details of the current authenticated user """
    current_user = await get_current_user_service(token_data)
    return current_user

# POST -> Registro de profesor
@router.post("/register_teacher",response_model=UserResponse,status_code=status.HTTP_201_CREATED, summary="Registers a new user with 'teacher' role.")
async def register_teacher_route(user: UserCreate):
    """
    Registers a new user with a 'teacher' role, without a specific
    admin privilege check for this initial version.
    """
    try:
        new_user = await register_teacher_service(user)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))