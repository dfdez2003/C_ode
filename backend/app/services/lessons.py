from schemas.lessons import LessonCreate, LessonUpdate, LessonOut, ModulePathOut
from models import PyObjectId
from db.db import lessons_collection, userprogress_collection
from typing import List, Optional
from bson import ObjectId
from schemas.exercises import ExerciseCreate, ExerciseOut
from services.exercises import create_one_exercise
from pydantic import BaseModel, Field
from fastapi import HTTPException, status

# Implementaciones de version sin incrustaciones
# Funciones internas para manejar las lecciones sin incrustaciones

async def create_lesson_service(lesson_data: LessonCreate) -> LessonOut:
    """
    Creates a new lesson with embedded exercises.
    """
    lesson_dict = lesson_data.model_dump()

    # Insertar el documento completo en la colección
    result = await lessons_collection.insert_one(lesson_dict)

    # Obtener el documento recién creado
    created_lesson = await lessons_collection.find_one({"_id": result.inserted_id})
    if created_lesson is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve created lesson.")
    
    # ✅ Convertir ObjectIds a strings recursivamente
    # cleaned_lesson_dict = convert_object_ids_to_str(created_lesson)

    # Convertir explícitamente el ObjectId a string para la salida
    created_lesson["_id"] = str(created_lesson["_id"])

    # También convierte el module_id a string
    if "module_id" in created_lesson and isinstance(created_lesson["module_id"], ObjectId):
        created_lesson["module_id"] = str(created_lesson["module_id"])

    # ✅ Validar y devolver el modelo
    return LessonOut.model_validate(created_lesson)



async def get_lesson_by_id_service(lesson_id: str) -> Optional[LessonOut]:
    """
    Retrieves a single lesson by its ID, including all its embedded exercises.
    """
    try:
        lesson_obj_id = ObjectId(lesson_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid lesson ID format.")
    
    lesson_dict = await lessons_collection.find_one({"_id": lesson_obj_id})
    if lesson_dict is None:
        return None
    # vamos a convertir el ObjectId a str
    lesson_dict["_id"] = str(lesson_dict["_id"])
    # También convierte el module_id a string
    if "module_id" in lesson_dict and isinstance(lesson_dict["module_id"], ObjectId):
        lesson_dict["module_id"] = str(lesson_dict["module_id"])
    
    return LessonOut.model_validate(lesson_dict)

async def update_lesson_service(lesson_id: str, lesson_data: LessonUpdate) -> Optional[LessonOut]:
    """
    Updates an existing lesson and its embedded exercises.
    """
    try:
        lesson_obj_id = ObjectId(lesson_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid lesson ID format.")

    # Convertir el esquema de actualización a un diccionario
    update_data = lesson_data.model_dump(exclude_unset=True)
    
    # Realizar la actualización atómica en la base de datos
    updated_lesson = await lessons_collection.find_one_and_update(
        {"_id": lesson_obj_id},
        {"$set": update_data},
        return_document=True
    )
    
    if updated_lesson is None:
        return None
    # Convertir el ObjectId a string para la salida
    updated_lesson["_id"] = str(updated_lesson["_id"])
    # También convierte el module_id a string
    if "module_id" in updated_lesson and isinstance(updated_lesson["module_id"], ObjectId):
        updated_lesson["module_id"] = str(updated_lesson["module_id"])
        
        
    return LessonOut.model_validate(updated_lesson)


async def delete_lesson_service(lesson_id: str) -> bool:
    """
    Deletes a lesson and all its embedded exercises.
    """
    try:
        lesson_obj_id = ObjectId(lesson_id)
    except:
        return False # O puedes lanzar una HTTPException
    
    result = await lessons_collection.delete_one({"_id": lesson_obj_id})
    return result.deleted_count > 0



# --------------------------------------------> Funciones pasadas 
async def create_lesson_basic(lesson_data: LessonCreate) -> LessonOut:
    # Creamos la lección con el modelo Pydantic
    lesson_model = LessonOut(**lesson_data.dict())
    # Insertamos en la base de datos
    result = await lessons_collection.insert_one(lesson_model.dict(by_alias=True))
    # Obtenemos la lección recién creada
    created_lesson = await lessons_collection.find_one({"_id": result.inserted_id})
    # Devolvemos la lección como un objeto Pydantic
    return LessonOut.parse_obj(created_lesson)

async def create_lesson_with_exercises(lesson_data: LessonCreate) -> LessonOut:
    # 1. Insertar la lección vacía
    lesson_dict = lesson_data.dict(exclude={"exercises"})
    lesson_dict["exercises"] = []
    result = await lessons_collection.insert_one(lesson_dict)
    lesson_id = result.inserted_id

    # 2. Crear los ejercicios
    exercise_ids: List[PyObjectId] = []
    for exercise in lesson_data.exercises:
        exercise.lesson_id = lesson_id
        created_exercise = await create_one_exercise(exercise)
        exercise_ids.append(created_exercise.id)  # ✅ ahora tenemos el id real del ejercicio

    # 3. Actualizar la lección con los IDs de ejercicios
    await lessons_collection.update_one(
        {"_id": lesson_id},
        {"$set": {"exercises": exercise_ids}}
    )

    # 4. Recuperar lección completa
    created_lesson = await lessons_collection.find_one({"_id": lesson_id})

    # 5. Devolver como LessonOut
    return LessonOut(
        id=created_lesson["_id"],
        title=created_lesson["title"],
        module_id=created_lesson["module_id"],
        description=created_lesson["description"],
        order=created_lesson["order"],
        xp_reward=created_lesson["xp_reward"],
        exercise_ids=exercise_ids,
        is_unlocked=False,
        is_completed=False,
    )



async def update_lesson_(lesson_id: PyObjectId, lesson_data: LessonUpdate) -> Optional[LessonOut]:
    """Actualiza una lección existente en la base de datos."""
    update_data = {k: v for k, v in lesson_data.dict().items() if v is not None}
    if not update_data:
        result = await lessons_collection.find_one({"_id": lesson_id})
        if result:
            return LessonOut.parse_obj(result)
        return None

    result = await lessons_collection.find_one_and_update(
        {"_id": lesson_id},
        {"$set": update_data},
        return_document=True
    )
    if result:
        return LessonOut.parse_obj(result)
    return None



# Pendiente 
async def get_all_lessons_path(user_id: PyObjectId) -> List[ModulePathOut]:
    """
    Retorna la estructura completa del camino de lecciones para el usuario,
    marcando el progreso y los desbloqueos.
    """
    # Lógica de ejemplo. En la realidad, deberías obtener el progreso del usuario
    # desde la colección `userprogress_collection`.
    user_progress_data = await userprogress_collection.find_one({"_id": user_id})
    
    # Asumimos que `user_progress_data` tiene un campo `completed_lessons`
    # que es una lista de IDs de lecciones completadas.
    completed_lessons = user_progress_data.get("completed_lessons", []) if user_progress_data else []

    all_lessons_cursor = lessons_collection.find({})
    all_lessons = await all_lessons_cursor.to_list(None)

    # Agrupa las lecciones por módulo
    modules = {}
    for lesson_data in all_lessons:
        module_id = lesson_data["module_id"]
        if module_id not in modules:
            # Aquí la lógica para determinar si el módulo está desbloqueado
            is_unlocked = True # Lógica simplificada
            modules[module_id] = {
                "id": module_id,
                "title": f"Módulo {module_id}",
                "is_unlocked": is_unlocked,
                "lessons": []
            }
        
        is_completed = str(lesson_data["_id"]) in completed_lessons
        
        # Aquí la lógica para determinar si la lección está desbloqueada
        is_unlocked = True # Lógica simplificada
        
        lesson_out = LessonOut(
            id=lesson_data["_id"],
            title=lesson_data["title"],
            module_id=lesson_data["module_id"],
            description=lesson_data.get("description"),
            order=lesson_data.get("order", 0),
            xp_reward=lesson_data.get("xp_reward", 0),
            is_unlocked=is_unlocked,
            is_completed=is_completed,
            exercise_ids=lesson_data.get("exercises", [])
        )
        modules[module_id]["lessons"].append(lesson_out)

    return [ModulePathOut(**m) for m in modules.values()]

async def get_user_current_progress(user_id: PyObjectId) -> Optional[dict]:
    """
    Obtiene el progreso actual de un usuario desde la base de datos.
    Esto es una función auxiliar que podría ser parte de un servicio
    de progreso del usuario más grande.
    """
    # Lógica simplificada para obtener el progreso.
    # Necesitas un esquema y un modelo para el progreso del usuario.
    # Aquí asumimos que tenemos una colección `userprogress_collection`.
    user_progress = await userprogress_collection.find_one({"_id": user_id})
    return user_progress

async def delete_lesson(lesson_id: str):
    return False

async def get_all_lessons() -> List[LessonOut]:
    return []


async def get_lesson_by_id(lesson_id: str) -> Optional[LessonOut]:
    if not ObjectId.is_valid(lesson_id):
        return None
    lesson = await lessons_collection.find_one({"_id": ObjectId(lesson_id)})    

async def update_lesson():
    return None