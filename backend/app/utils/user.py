from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError
from motor.motor_asyncio import AsyncIOMotorDatabase
from schemas.users import UserResponse
from db.db import get_database


# Variables de configuración de la app
SECRET_KEY = "df4720350"  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180

# Esquema para la carga útil del token
class TokenData(BaseModel):
    username: Optional[str] = None
    id: Optional[str] = None  # ID del usuario (MongoDB ObjectId como string)
    role: Optional[str] = None
    

# Instancia de OAuth2 para manejar los tokens en los headers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

# Función para crear tokens de acceso
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Crea un token de acceso JWT con una fecha de expiración.
    """
    # Copia los datos para no modificar el original
    to_encode = data.copy()
    # Calcula la fecha de expiración
    if expires_delta:
        # Si se proporciona un delta, úsalo
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Si no, usa el valor por defecto
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Añade la fecha de expiración a los datos a codificar
    to_encode.update({"exp": expire})
    # Firma y codifica el token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Función para obtener el usuario actual a partir del token
def get_current_user_from_token(token: str = Depends(oauth2_scheme)):
    """
    Decodifica el token para obtener los datos del usuario.
    """
    # Manejo de errores de autenticación
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Intenta decodificar el token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Extrae el nombre de usuario, ID y rol del payload
        username: str = payload.get("sub")
        user_id: str = payload.get("id")
        role: str = payload.get("role")
        # Verifica que todos los valores estén presentes
        if username is None or user_id is None or role is None:
            raise credentials_exception
        # Valida y retorna los datos del token
        token_data = TokenData(username=username, id=user_id, role=role)
    except JWTError:
        raise credentials_exception
    return token_data

async def require_teacher_role(current_user: TokenData = Depends(get_current_user_from_token)):
    """
    Dependency that checks if the authenticated user has the 'teacher' role.
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted for this user role."
        )
    return current_user

async def get_current_user(
    token_data: TokenData = Depends(get_current_user_from_token), # Usa tu función existente
    db: AsyncIOMotorDatabase = Depends(get_database) # Inyecta la base de datos
) -> UserResponse:
    """
    Dependency that retrieves the full User object (including the MongoDB ID)
    from the database using the username from the JWT payload.
    """
    username = token_data.username
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing username payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Buscar al usuario en la colección 'users'
    user_doc = await db["users"].find_one({"username": username})
    
    if user_doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # 2. Convertir el documento de MongoDB a UserResponse
    # Aseguramos que el _id se serialice a 'id' (str)
    user_doc['id'] = str(user_doc['_id'])
    
    try:
        # Usamos el esquema de respuesta para validar y retornar el objeto limpio
        return UserResponse(**user_doc)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User data serialization error.")

"""
SECRET_KEY: Se centraliza y se advierte sobre su seguridad.
TokenData: Creamos un esquema Pydantic para la carga útil (payload) del token. Esto nos permite usar la validación de Pydantic 
para asegurar que el token tenga la información necesaria (username y ahora también role).
oauth2_scheme: Esta es una clase de FastAPI que facilita la extracción del token del header de la petición HTTP.
get_current_user_from_token: Esta función es la dependencia de seguridad. Se encarga de decodificar el token, 
manejar los errores de forma adecuada con HTTPException (por si el token es inválido o ha expirado) y devolver los datos del usuario. 
El rol del usuario se recupera del token, lo que nos permitirá implementar la autorización de roles fácilmente.
"""