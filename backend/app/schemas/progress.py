# backend/app/schemas/progress.py

from typing import Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from models import PyObjectId
from bson import ObjectId

# --- Esquemas de Entrada (Input) ---

class ExerciseSubmission(BaseModel):
    """Datos enviados por el frontend para registrar un intento de ejercicio."""
    session_id: str = Field(..., description="ID de la sesión de estudio activa (CRÍTICO para la racha)")
    exercise_uuid: str = Field(..., description="UUID del ejercicio incrustado.")
    user_response: Any = Field(..., description="La respuesta del usuario (string, código, array, etc.)")
    module_id: str = Field(..., description="ID del módulo padre (para referencia)")
    lesson_id: str = Field(..., description="ID de la lección padre (para referencia)")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "60c72b1f9b3e6c3a1d9b3e6c",
                "exercise_uuid": "9222dd95-6621-48e7-bc1e-888e44c2e012",
                "user_response": "Operador &&", # Ejemplo de respuesta de Opción Múltiple
                "module_id": "68ee776a0fa3f0e9c3939692",
                "lesson_id": "68ee77b80fa3f0e9c3939695"
            }
        }


# --- Esquema de la Colección (UserProgress) ---

# Ejercicio individual dentro del intento de lección
class ExerciseAttempt(BaseModel):
    """Intento individual de un ejercicio dentro de una lección."""
    exercise_uuid: str
    user_response: Any
    is_correct: bool
    points_earned: int
    attempt_time: datetime = Field(default_factory=datetime.utcnow)

# Progreso completo de una LECCIÓN (reemplaza el modelo anterior)
class LessonProgress(BaseModel):
    """Estructura del progreso de una LECCIÓN completa (mejor intento)."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    module_id: str
    lesson_id: str
    
    # Intento actual
    session_id: str  # ID de la sesión del último intento
    exercises: List[ExerciseAttempt] = []  # Ejercicios completados en este intento
    
    # Puntajes
    current_score: int = 0  # Puntaje del intento actual
    best_score: int = 0     # Mejor puntaje histórico
    total_possible: int = 0 # Puntaje máximo posible de la lección
    
    # Metadata
    attempt_count: int = 1  # Número de intentos realizados
    first_attempt: datetime = Field(default_factory=datetime.utcnow)
    last_attempt: datetime = Field(default_factory=datetime.utcnow)
    is_completed: bool = False  # True cuando termina todos los ejercicios
    
    # Para exámenes/lecciones privadas
    is_locked: bool = False  # True si es un examen de un solo intento
    
    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},
        "arbitrary_types_allowed": True
    }

# MANTENER UserProgress para compatibilidad con código existente (DEPRECATED)
class UserProgress(BaseModel):
    """DEPRECATED: Usar LessonProgress en su lugar."""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    session_id: str
    exercise_uuid: str
    module_id: str
    lesson_id: str
    attempt_time: datetime = Field(default_factory=datetime.utcnow)
    user_response: Any
    score: int
    status: str = Field(..., description="completed, in_progress, failed")
    
    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},
        "arbitrary_types_allowed": True
    }


# --- Esquema de Respuesta (Output) ---

class ProgressResponse(BaseModel):
    """Respuesta de retroalimentación para el frontend."""
    is_correct: bool = Field(..., description="True si la respuesta fue validada como correcta.")
    lesson_finished: bool = Field(..., description="True si se completaron todos los ejercicios de la lección.")
    points_earned: int = Field(..., description="XP o puntos otorgados en este intento.")
    current_score: int = Field(default=0, description="Puntaje actual del intento en curso.")
    total_possible: int = Field(default=0, description="Puntaje máximo posible de la lección.")
    #  Campos adicionales para make_code
    code_feedback: Optional[dict] = Field(default=None, description="Feedback detallado para ejercicios de código")
    # Estructura: {"code_is_correct": bool, "test_is_correct": bool, "has_tests": bool}


class UserProgressOut(BaseModel):
    """Esquema de salida para los registros de progreso que se devolverán al cliente."""
    id: str = Field(alias="_id", description="ID del registro de progreso")
    user_id: str
    session_id: str
    exercise_uuid: str
    module_id: str
    lesson_id: str
    attempt_time: datetime
    user_response: Any
    score: int
    status: str

    model_config = {
        "json_encoders": {ObjectId: str}
    }

class UserProgressSummary(BaseModel):
    """Estructura de la respuesta GET /progress/user/{user_id}."""
    
    # Datos de User (para el Dashboard)
    user_id: str
    username: str
    total_points: int
    current_streak_days: int = Field(alias="streak.current_days")
    
    # Datos de Progreso (para marcar ejercicios completados)
    completed_exercises: list[str] = Field(..., description="Lista de UUIDs de ejercicios completados.")
    
    class Config:
        # Aseguramos que podemos acceder a campos anidados como 'streak.current_days'
        json_encoders = {ObjectId: str}
        populate_by_name = True