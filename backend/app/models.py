from pydantic import BaseModel, EmailStr, Field, GetCoreSchemaHandler
from datetime import datetime
from bson import ObjectId  
from typing import Optional, List,Dict, Union,Any
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue
import uuid

# Clase personalizada para manejar ObjectId de MongoDB en Pydantic v2
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        return core_schema.general_plain_validator_function(cls.validate)
    
    @classmethod
    def validate(cls, v, _info):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        # Si ya es ObjectId, devolverlo directamente
        if isinstance(v, ObjectId):
            return v
        # Si es string, convertirlo a ObjectId
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler):
        return handler(core_schema.str_schema())

# ---> Casos prueba de ejercicios de codigo <---
class ExerciseTestCases_Model(BaseModel):
    input: str  
    expected_output: str  

# --> Modelo base de ejercicio (común a todos los tipos)<---
class ExerciseBaseModel(BaseModel):
    exercise_id: str = Field(default_factory=lambda: str(uuid.uuid4()))  
    type: str 
    title: str 
    points: int  

    # Configuración de Pydantic v2 para manejo de tipos especiales
    model_config = {
        "arbitrary_types_allowed": True,  # Permite tipos personalizados como PyObjectId
        "json_encoders": {ObjectId: str},  # Convierte ObjectId a string en JSON
        "from_attributes": True  # Permite crear instancias desde atributos de objetos
    }

# ---> Tipos de ejercicios <---
class StudyExercise_Model(ExerciseBaseModel):
    type: str = "study" 
    flashcards: Dict[str, str] 


class CompleteExercise_Model(ExerciseBaseModel):           
    type: str = "complete" 
    text: str  
    options: List[str]  
    correct_answer: str  

class MakeCodeExercise_Model(ExerciseBaseModel):
    type: str = "make_code"  
    description: str  
    code: str  
    solution: str 
    test_cases: List[ExerciseTestCases_Model] # Lista de casos de prueba

class QuestionExercise_Model(ExerciseBaseModel):
    type: str = "question"  
    description: str 
    options: List[str] 
    correct_answer: str 


class UnitConceptsExercise_Model(ExerciseBaseModel):
    type: str = "unit_concepts" 
    description: str  
    concepts: Dict[str, str]  



# ------> Union para ejercicios <------
# Esta unión permite trabajar con cualquier tipo de ejercicio de manera polimórfica
ExerciseModel = Union[
    StudyExercise_Model,        # Ejercicios de estudio con flashcards
    CompleteExercise_Model,     # Ejercicios de completar espacios
    MakeCodeExercise_Model,     # Ejercicios de programación
    QuestionExercise_Model,     # Ejercicios de opción múltiple
    UnitConceptsExercise_Model  # Ejercicios de conceptos de unidad
]

# ---> Modelo de lección que contiene ejercicios <---               
class LessonModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")  # ID único, opcional para creación
    module_id: PyObjectId  # Referencia al módulo padre
    title: str  # Título descriptivo de la lección
    description: str  # Descripción detallada del contenido de la lección
    order: int  # Orden de la lección dentro del módulo (1, 2, 3, etc.)
    xp_reward: int  # Recompensa en puntos XP por completar la lección
    exercises: List[ExerciseModel] = [] # Lista de los ejercicios de esta lección

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "from_attributes": True
    }

# ---> Modelo de módulo que contiene lecciones <---
class ModuleModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")  # ID único, opcional para creación
    title: str  # Título del módulo
    description: str  # Descripción detallada del contenido
    order: int  # Orden del módulo en el curso
    estimate_time: int  # usamos int por que se habla de "dias" y no es tan exacto
    lessons: List[LessonModel] = [] # Lista de IDs de lecciones en este módulo

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "from_attributes": True
    }

# ---> Progreso del usuario en un ejercicio <---
class UserProgressAttempt_Model(BaseModel):
    code: str  # Código escrito por el usuario
    is_correct: bool  # Si el intento fue correcto
    submitted_at: datetime  # Timestamp del intento

# ---> Modelo de progreso del usuario <---
class UserProgress_Model(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")  # ID único del progreso
    user_id: PyObjectId  # Referencia al usuario
    module_id: PyObjectId  # Referencia al módulo
    lesson_id: PyObjectId  # Referencia a la lección
    exercise_uuid: str # Referencia al UUID único del ejercicio incrustado
    status: str  # Estado: "not_started", "in_progress", "completed"
    attempts: List[UserProgressAttempt_Model] = []  # Historial de intentos
    last_session_id: Optional[PyObjectId] = None  # Última sesión de trabajo
    is_mastered: bool = False  # Si el ejercicio ha sido dominado

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "from_attributes": True
    }

# ---> Modelo de sesión de estudio <---
class SessionModel(BaseModel):      
    id: Optional[PyObjectId] = Field(alias="_id")  # ID único de la sesión
    user_id: PyObjectId  # Referencia al usuario
    lesson_id: PyObjectId  # Referencia a la lección
    start_time: datetime  # Momento de inicio de la sesión
    end_time: Optional[datetime] = None  # Momento de fin (None si está activa)
    duration_minutes: Optional[float] = None  # Duración en minutos
    status: str = "in_progress"  # Estado de la sesión
    exercises_completed: int = 0  # Ejercicios completados en esta sesión
    total_points_gained: int = 0  # Puntos ganados en esta sesión

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "from_attributes": True
    }

# ----> Modelo de recompensa <---
class RewardModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")  # ID único de la recompensa
    name: str  # Nombre de la recompensa
    description: str  # Descripción de la recompensa
    type: str  # Tipo de recompensa
    points: int  # Puntos que otorga la recompensa
    users_awarded: List[PyObjectId] = []  # Usuarios que ya la obtuvieron

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "from_attributes": True
    }

# ---> Racha de estudio del usuario <---
class UserStreakModel(BaseModel):
    current_days: int = 0  # Días consecutivos estudiando
    last_practice_date: Optional[datetime] = None  # Último día de estudio

# ---> Modelo de usuario <---
class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")  # ID único del usuario
    username: str  # Nombre de usuario único
    email: str  # Correo electrónico
    password_hash: str  # Hash de la contraseña (seguro)
    role: str = "student"  # Rol del usuario
    created_at: datetime = datetime.now()  # Fecha de registro
    streak: UserStreakModel = UserStreakModel()  # Racha de estudio
    total_points: int = 0  # Puntos totales acumulados
    last_session_id: Optional[PyObjectId] = None  # Última sesión

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "from_attributes": True
    }
