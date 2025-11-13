from schemas.exercises import ExerciseCreate, ExerciseOut
from db.db import exercises_collection
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
    
    # Retornar el documento aplanado
    return {**exercise_dict, **specific_data}

async def create_exercise_(exercise_data: ExerciseCreate) -> ExerciseOut:
    """
    Servicio para crear un ejercicio individual.
    Retorna el ejercicio creado como un objeto ExerciseOut.
    """
    return None

# ---> CRUD ATÓMICO (Llamado desde services/lessons.py) --- interno ---
async def create_one_exercise(exercise_data: ExerciseCreate) -> ExerciseOut:
    """
    Crea un único ejercicio en la base de datos.
    Retorna el ejercicio creado como un objeto ExerciseOut.
    """
    # 1. Prepara el documento aplanado
    document_to_insert = _prepare_exercise_document(exercise_data)
    
    # 2. Inserta el documento
    result = await exercises_collection.insert_one(document_to_insert)
    
    # 3. Recupera el documento insertado
    created_doc = await exercises_collection.find_one({"_id": result.inserted_id})
    
    # 4. Parsea y retorna
    return ExerciseOut.model_validate(created_doc)

async def update_one_exercise(exercise_id: str, update_data: Dict[str, Any]) -> Optional[ExerciseOut]:
    """
    Actualiza los datos de un único ejercicio existente por su ID.
    Los datos de actualización ya deben estar aplanados (sin el campo 'data').
    """
    if not ObjectId.is_valid(exercise_id):
        return None

    # 1. Limpiar el diccionario de actualización (remover campos None)
    update_fields = {k: v for k, v in update_data.items() if v is not None}
    if not update_fields:
        return await get_exercise_by_id(exercise_id) # No hay cambios, devuelve el actual

    # Nota: No necesitamos aplanar si el servicio de Lecciones ya lo hace,
    # pero asumimos que el diccionario de entrada aquí ya es el conjunto final de campos.

    # 2. Ejecutar la actualización en MongoDB
    result = await exercises_collection.find_one_and_update(
        {"_id": ObjectId(exercise_id)},
        {"$set": update_fields},
        return_document=True
    )
    if result:
        # Usamos ExerciseOut para el esquema de respuesta
        return ExerciseOut.parse_obj(result)
    return None


async def delete_one_exercise(exercise_id: str) -> bool:
    """
    Elimina un único ejercicio específico por su ID.
    """
    if not ObjectId.is_valid(exercise_id):
        return False
    
    result = await exercises_collection.delete_one({"_id": ObjectId(exercise_id)})
    return result.deleted_count > 0


async def delete_all_by_lesson_id(lesson_id: PyObjectId) -> int:
    """
    Elimina todos los ejercicios asociados a un lesson_id (eliminación en cascada).
    Retorna el número de documentos eliminados.
    """
    result = await exercises_collection.delete_many({"lesson_id": lesson_id})
    return result.deleted_count


# ---> FUNCIONES DE LECTURA (Usadas por Lesson Service y Routers) <--- interno ---
async def get_exercise_by_id(exercise_id: str) -> Optional[ExerciseOut]:
    """
    Obtiene un ejercicio por su ID, usando el esquema de salida genérico.
    """
    if not ObjectId.is_valid(exercise_id):
        return None
    exercise_data = await exercises_collection.find_one({"_id": ObjectId(exercise_id)})
    if exercise_data:
        # Usamos ExerciseOut para el esquema de respuesta que incluye el campo 'data'
        # reestructurado.
        return ExerciseOut.parse_obj(exercise_data)
    return None

async def get_exercise_strict(exercise_id: str) -> Optional[ExerciseModel]:
    """
    Obtiene un ejercicio por su ID con validación estricta de tipo 
    (usando la Union de modelos ExerciseModel).
    """
    if not ObjectId.is_valid(exercise_id):
        return None
        
    exercise_data = await exercises_collection.find_one({"_id": ObjectId(exercise_id)})

    if exercise_data:
        # Usamos ExerciseModel (la Union de Pydantic) para parsear el documento
        return ExerciseModel.parse_obj(exercise_data)
    return None

async def get_exercises_by_lesson_id(lesson_id: PyObjectId) -> List[ExerciseOut]:
    """
    Obtiene todos los ejercicios asociados a una lección específica.
    """
    cursor = exercises_collection.find({"lesson_id": lesson_id})
    exercises_data = await cursor.to_list(length=None)
    
    # Mapea los resultados al esquema de salida
    return [ExerciseOut.parse_obj(data) for data in exercises_data]