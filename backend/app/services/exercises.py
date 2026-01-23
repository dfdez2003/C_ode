from schemas.exercises import ExerciseCreate, ExerciseOut
import uuid
from typing import List, Optional, Dict, Any
from bson import ObjectId
from models import ExerciseModel, PyObjectId 

# -------------------> Funciones de Servicio para Ejercicios <-------------------
# Implementacion desde modulos CRUD atomicos internos.

# ---> FUNCIONES AUXILIARES <---
def _prepare_exercise_document(exercise_data: ExerciseCreate) -> Dict[str, Any]:
    """
    Función auxiliar para aplanar el esquema de entrada (ExerciseCreate)
    en un diccionario listo para MongoDB.
    """
    exercise_dict = exercise_data.dict()
    
    # 1. El lesson_id ya es PyObjectId, no necesitamos validación adicional
    # exercise_dict["lesson_id"] ya es PyObjectId
    
    # 2. Aplanamos el campo 'data' (contiene los campos específicos del tipo de ejercicio)
    specific_data = exercise_dict.pop("data", {})
    
    # Asegurar que exista un exercise_uuid en el documento (medida de seguridad)
    exercise_dict.setdefault("exercise_uuid", str(uuid.uuid4()))

    # Retornar el documento aplanado
    return {**exercise_dict, **specific_data}

# ---> CRUD ATÓMICO (Llamado desde services/modules.py) --- interno ---
async def create_one_exercise(exercise_data: ExerciseCreate) -> ExerciseOut:
    """
    Crea un único ejercicio incrustado en una lección dentro de un módulo.
    Retorna el ejercicio creado como un objeto ExerciseOut.
    """
    # 1. Prepara el documento aplanado
    document_to_insert = _prepare_exercise_document(exercise_data)
    
    # Nota: Este documento se inserta como parte de un array embebido
    # en el documento de lección, no como colección separada
    return ExerciseOut.model_validate(document_to_insert)

async def get_exercises_by_lesson_id(lesson_id: PyObjectId) -> List[ExerciseOut]:
    """
    Obtiene todos los ejercicios asociados a una lección específica.
    Nota: En arquitectura actual, los ejercicios están embebidos en lecciones,
    no en colección separada. Esta función es referencia para compatibilidad.
    """
    # En la arquitectura actual (incrustación), esta función 
    # se maneja desde modules.py extrayendo del array embebido
    return []