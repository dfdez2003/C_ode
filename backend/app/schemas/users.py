from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
from models import UserStreakModel 

# ---> Esquema base <---
class UserBase(BaseModel):
    username: str
    email: EmailStr

#  Esquemas de entrada (INPUT) 
# Se usa para la creación de un nuevo usuario (POST /users/register).
class UserCreate(UserBase):
    password: str

# ---> Esquema de entrada para login <---
# Se usa para el inicio de sesión del usuario (POST /users/login).
class UserLogin(BaseModel):
    username: str
    password: str

# ---> Esquema de actualización (UPDATE) <---   (sin implementacion aun)
# Se usa para la actualización del perfil del usuario (PUT /users/{id}).
# Todos los campos son opcionales. No incluye la contraseña por seguridad.
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

# ---> Esquema de actualización de contraseña <--- ( sin implementacion aun)
# Se usa para el cambio de contraseña (PUT /users/{id}/password).
# Es un esquema separado para una intención clara y mayor seguridad. 
class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

# -------------------> ESQUEMAS DE SALIDA (OUTPUT) <--------------
# Se usa para la respuesta de la API al cliente.
class UserResponse(UserBase):
    id: str
    role: str
    created_at: datetime
    streak: UserStreakModel
    total_points: int
    last_session_id: Optional[str]

    model_config = {
        "from_attributes": True  # Permite mapear de un objeto de base de datos a un esquema Pydantic.
    }

# -------------------> ESQUEMAS DE AUTENTICACIÓN <--------------
# Se utiliza para validar las credenciales deloginl token JWT.
class Token(BaseModel):
    access_token: str
    token_type: str

# Contiene la carga útil (payload) del token.
class TokenData(BaseModel):
    username: Optional[str] = None

class UserStreak(BaseModel):
    current_days: int = 0
    last_practice_date: Optional[datetime] = None

