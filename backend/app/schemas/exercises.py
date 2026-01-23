from pydantic import BaseModel, Field
from bson import ObjectId
from models import PyObjectId
from typing import List, Dict, Optional, Union
from typing import Any
import uuid

# ---> Esquema para pruebas <------
class ExerciseTestCases(BaseModel):
    input: str  # Entrada del caso de prueba
    expected_output: str  # Salida esperada del caso de prueba


# ----> Modelo base <------
class ExerciseBase(BaseModel):
    # Usamos un UUID como identificador único para el sub-documento.
    exercise_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  
    title: str 
    points: int  
    
# Esquemas para creación y salida de ejercicios ( uso interno )
# -----------------------------------------------------------------------
class ExerciseCreate(BaseModel):
    # Añadimos `exercise_uuid` para asegurar que todo ejercicio creado tenga UUID desde el momento de creación
    exercise_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lesson_id: Optional[PyObjectId]= None # ID de la lección padre
    type: str  # Tipo de ejercicio
    title: str  # Título del ejercicio
    points: int  # Puntos que otorga
    data: Dict[str, Any]  # Datos específicos del tipo de ejercicio
class ExerciseOut(ExerciseBase):
    data: Dict[str, Any]  # Datos específicos del tipo de ejercicio
    class Config:
        populate_by_name = True
# ------------------------------------------------------------------------

# ------------Modelos específicos para cada tipo de ejercicio------------

class StudyExerciseSchema(ExerciseBase):
    type: str = "study"
    flashcards: Dict[str, str]

class CompleteExerciseSchema(ExerciseBase):
    type: str = "complete"
    text: str
    options: List[str]
    correct_answer: str

class MakeCodeExerciseSchema(ExerciseBase):
    type: str = "make_code"
    description: str  # Enunciado del problema
    code: str
    solution: str
    test_cases: List[ExerciseTestCases]

class QuestionExerciseSchema(ExerciseBase):
    type: str = "question"
    description: str  # Enunciado de la pregunta
    options: List[str]
    correct_answer: str

class UnitConceptsExerciseSchema(ExerciseBase):
    type: str = "unit_concepts"
    concepts: Dict[str, str]  # { concepto: definición }


# Unión de todos los tipos de ejercicios
# Pydantic intentará validar contra cada esquema hasta encontrar uno que coincida
# Las validaciones específicas de campos requeridos se manejan en services/modules.py
ExerciseSchema = Union[
    StudyExerciseSchema,
    CompleteExerciseSchema,
    MakeCodeExerciseSchema,
    QuestionExerciseSchema,
    UnitConceptsExerciseSchema,
]

