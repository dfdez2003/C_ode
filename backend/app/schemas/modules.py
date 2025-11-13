from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from models import PyObjectId
from bson import ObjectId

# Importamos la Union de esquemas de lecciones que acabamos de rediseñar
from schemas.lessons import LessonBaseSchema, LessonUpdate, LessonOut,LessonCreate # Asegúrate de importar el esquema LessonOut


# --- Esquema de Creación (Input) ---
class ModuleCreate(BaseModel):
    title: str
    description: str
    order: int
    estimate_time: int
    lessons: List[LessonCreate] = Field(..., min_items=1)


# --- Esquema de Actualización (Input) ---
# Ahora la lista de lecciones usa el esquema de actualización
class ModuleUpdate(BaseModel):
    id: Optional[str] = None 
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    estimate_time: Optional[int] = None
    lessons: Optional[List[LessonUpdate]] = None # <--- ¡El cambio clave!

# --- Esquema de Salida (Output) ---
class ModuleOut(BaseModel):
    id: str = Field(alias="_id")
    title: str
    description: str
    order: int
    estimate_time: int
    lessons: List[LessonOut]

    model_config = {
        "from_attributes": True,
        "json_encoders": {ObjectId: str},
    }