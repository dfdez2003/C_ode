from pydantic import BaseModel, Field
from typing import Optional, List
from schemas.exercises import ExerciseSchema 
from models import PyObjectId
from bson import ObjectId

# --- Clase Base para Lecciones ---
class LessonBaseSchema(BaseModel):
    title: str
    description: str
    order: int
    xp_reward: int
    is_private: bool = False  # True si es una lección privada/examen (un solo intento)
    # lista de ejercicios embebida
    exercises: List[ExerciseSchema] = Field(..., min_items=1, description="Must contain at least one exercise.")
    

# --- Esquema de Creación---
# este esquema es similar al base, pero se puede extender si es necesario
class LessonCreate(LessonBaseSchema):
    """Para este esquema solo agregaremos el id del modulo, ya que es requerido."""
    pass


# --- Esquema de Actualización ---
# este es de los mas importantes, ya que es el que se usa para actualizar las lecciones
# y como vemos todos los campos son opcionales, ya que no siempre se van a actualizar todos los campos
class LessonUpdate(BaseModel):
    """Esquema utilizado para actualizar campos opcionales de una lección."""
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    xp_reward: Optional[int] = None
    is_private: Optional[bool] = None  #  Permitir cambiar el estado privado/público
    # Permite actualizar la lista completa de ejercicios
    exercises: Optional[List[ExerciseSchema]] = None

# --- Esquema de Salida ---
"""Este es el esquema que usaremos para todas las respuestas de la API 
(GET, POST, PUT). Será un reflejo de nuestro modelo de base de datos. 
En lugar de una lista de ids de ejercicios, contendrá la lista de objetos 
de ejercicios completos"""
class LessonOut(LessonBaseSchema):
    id: str = Field(..., alias="_id")
    module_id: str
    # lista de ejercicios embebida
    exercises: List[ExerciseSchema]

    model_config = {
        "from_attributes": True,
        "json_encoders": {ObjectId: str},
    }

# --------------------------------------------------- Pendiente ---------------------------------------------------
# --- Esquema de la Ruta del Curso ---
# sin uso actual pero se piensa que es necesario, ya que se usara a la par de los modulos
class ModulePathOut(BaseModel):
    """Esquema para la visualización del camino de aprendizaje agrupado por módulos."""
    id: PyObjectId
    title: str
    is_unlocked: bool
    lessons: List[LessonOut]

    
