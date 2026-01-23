from typing import Optional, List, Any, Set
from bson import ObjectId
from fastapi import HTTPException, status

from schemas.modules import ModuleCreate, ModuleUpdate, ModuleOut
from schemas.lessons import LessonCreate
from db.db import modules_collection

# Función auxiliar para convertir ObjectIds a strings recursivamente
def convert_object_ids_to_str(obj: Any) -> Any:
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, list):
        return [convert_object_ids_to_str(item) for item in obj]
    if isinstance(obj, dict):
        return {key: convert_object_ids_to_str(value) for key, value in obj.items()}
    return obj

# ========== VALIDACIONES ==========

def validate_module_lessons(lessons: List[dict]) -> None:
    """
    Valida que las lecciones de un módulo cumplan con las reglas de integridad:
    - Cada lección debe tener al menos un ejercicio
    - Los exercise_uuid deben ser únicos dentro de cada lección
    - Los campos requeridos según el tipo de ejercicio deben estar presentes
    """
    if not lessons:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un módulo debe tener al menos una lección."
        )
    
    for idx, lesson in enumerate(lessons):
        lesson_title = lesson.get("title", f"Lección #{idx + 1}")
        exercises = lesson.get("exercises", [])
        
        # Validar que la lección tenga al menos un ejercicio
        if not exercises:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La lección '{lesson_title}' debe tener al menos un ejercicio."
            )
        
        # Validar unicidad de exercise_uuid dentro de la lección
        exercise_uuids: Set[str] = set()
        for ex_idx, exercise in enumerate(exercises):
            ex_uuid = exercise.get("exercise_uuid")
            ex_type = exercise.get("type")
            ex_title = exercise.get("title", f"Ejercicio #{ex_idx + 1}")
            
            if not ex_uuid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El ejercicio '{ex_title}' en la lección '{lesson_title}' no tiene exercise_uuid."
                )
            
            if ex_uuid in exercise_uuids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Duplicado: exercise_uuid '{ex_uuid}' en la lección '{lesson_title}'."
                )
            exercise_uuids.add(ex_uuid)
            
            # Validar campos requeridos según el tipo
            validate_exercise_fields(exercise, ex_type, ex_title, lesson_title)

def validate_exercise_fields(exercise: dict, ex_type: str, ex_title: str, lesson_title: str) -> None:
    """
    Valida que un ejercicio tenga los campos requeridos según su tipo.
    """
    required_base = ["type", "title", "points"]
    for field in required_base:
        if field not in exercise or exercise[field] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El ejercicio '{ex_title}' en la lección '{lesson_title}' no tiene el campo requerido '{field}'."
            )
    
    # Validar campos específicos por tipo
    type_requirements = {
        "study": ["flashcards"],
        "complete": ["text", "options", "correct_answer"],
        "make_code": ["description", "code", "solution", "test_cases"],
        "question": ["description", "options", "correct_answer"],  # description = enunciado
        "unit_concepts": ["concepts"]
    }
    
    if ex_type not in type_requirements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de ejercicio '{ex_type}' no válido en '{ex_title}' (Lección: '{lesson_title}')."
        )
    
    for field in type_requirements[ex_type]:
        if field not in exercise or exercise[field] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El ejercicio '{ex_title}' de tipo '{ex_type}' en la lección '{lesson_title}' no tiene el campo requerido '{field}'."
            )

# CREATE -> Crear un modulo con lecciones y ejercicios incrustados
async def create_module_service(module_data: ModuleCreate) -> ModuleOut:
    """
    Crea un nuevo modulo con lecciones y ejercicios incrustados,
    generando los ObjectIds de las lecciones antes de la inserción.
    Incluye validaciones de integridad de datos.
    """
    module_dict = module_data.model_dump()
    
    # 1. Validar integridad de lecciones y ejercicios
    validate_module_lessons(module_dict.get("lessons", []))
    
    # 2. Generar el ObjectId para el modulo (lo usaremos para el module_id en las lecciones)
    module_id = ObjectId()
    module_dict["_id"] = module_id
    
    # 3. Generar IDs para cada lección incrustada
    for lesson in module_dict.get("lessons", []):
        # Asigna un _id único a la lección incrustada (necesario para la validación de LessonOut)
        lesson["_id"] = ObjectId() 
        # Inyecta el ID del modulo en la lección incrustada (para coherencia)
        lesson["module_id"] = module_id
    
    # 4. Insertar el documento completo
    result = await modules_collection.insert_one(module_dict)
    
    # 5. Obtener y limpiar para la salida
    created_module = await modules_collection.find_one({"_id": result.inserted_id})
    if not created_module:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created module."
        )

    # Convertir ObjectIds a strings recursivamente
    cleaned_module_dict = convert_object_ids_to_str(created_module)
    return ModuleOut.model_validate(cleaned_module_dict)

# READ -> Obtener un modulo con lecciones y ejercicios incrustados por id 
async def get_module_by_id_service(module_id: str) -> Optional[ModuleOut]:
    """
    Obtiene un modulo por su ID, incluyendo todas sus lecciones y ejercicios.
    """
    try:
        module_obj_id = ObjectId(module_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid module ID format.")
    
    module_dict = await modules_collection.find_one({"_id": module_obj_id})
    if not module_dict:
        return None
    
    cleaned_module_dict = convert_object_ids_to_str(module_dict)
    
    return ModuleOut.model_validate(cleaned_module_dict)

# UPDATE -> Actualizar un modulo con lecciones y ejercicios incrustados

async def update_module_service(module_id: str, update_data: ModuleUpdate) -> Optional[ModuleOut]:
    """
    Updates an existing module and its embedded lessons by replacing the entire
    lessons array with the new data. This allows for additions, removals, and updates.
    Incluye validaciones de integridad de datos.
    """
    try:
        module_obj_id = ObjectId(module_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid module ID format.")

    # 1. Obtener el modulo actual para fusionar los datos
    existing_module = await modules_collection.find_one({"_id": module_obj_id})
    if not existing_module:
        return None # modulo no encontrado

    # 2. Convertir la entrada del usuario a un diccionario
    update_dict = update_data.model_dump(exclude_unset=True)

    # 3. Validar lecciones si se están actualizando
    if "lessons" in update_dict and update_dict["lessons"]:
        validate_module_lessons(update_dict["lessons"])

    # 4. Fusionar los datos existentes con los nuevos
    # Usaremos una copia del documento para no modificar el original
    merged_data = existing_module.copy()
    
    # Actualizar los campos de nivel superior (title, order, etc.)
    merged_data.update(update_dict)
    
    # Manejar la lista de lecciones si se envió
    if "lessons" in update_dict:
        # Reemplazar la lista completa de lecciones con la nueva
        lessons_list = update_dict["lessons"]
        # Generar IDs para las lecciones que no los tienen (nuevas)
        for lesson_data in lessons_list:
            # Si la lección ya tiene _id (viene de MongoDB), convertirlo a ObjectId
            if lesson_data.get("_id"):
                if isinstance(lesson_data["_id"], str):
                    lesson_data["_id"] = ObjectId(lesson_data["_id"])
            else:
                # Lección nueva, generar ID
                lesson_data["_id"] = ObjectId()
            
            # Asegurar que tenga module_id
            lesson_data["module_id"] = module_obj_id
        
        merged_data["lessons"] = lessons_list
        
    # 5. Reemplazar el documento completo en la base de datos
    await modules_collection.replace_one(
        {"_id": module_obj_id},
        merged_data
    )
    
    # 6. Obtener el documento final y retornarlo
    updated_module = await modules_collection.find_one({"_id": module_obj_id})
    
    cleaned_module_dict = convert_object_ids_to_str(updated_module)
    return ModuleOut.model_validate(cleaned_module_dict)


# DELETE -> Eliminar un modulo por completo ( uso interno )
async def delete_module_service(module_id: str) -> bool:
    """
    Elimina un modulo y todas sus lecciones y ejercicios incrustados.
    """
    try:
        module_obj_id = ObjectId(module_id)
    except:
        return False
        
    result = await modules_collection.delete_one({"_id": module_obj_id})
    return result.deleted_count > 0

# ADD LESSON -> Agregar una nueva lección a un módulo existente
async def add_lesson_to_module_service(module_id: str, lesson_data: LessonCreate) -> Optional[ModuleOut]:
    """
    Agrega una nueva lección con sus ejercicios a un módulo existente.
    Valida que la lección tenga al menos un ejercicio antes de agregarla.
    """
    try:
        module_obj_id = ObjectId(module_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid module ID format.")

    # 1. Verificar que el módulo existe
    existing_module = await modules_collection.find_one({"_id": module_obj_id})
    if not existing_module:
        return None  # Módulo no encontrado

    # 2. Convertir lesson_data a diccionario y validar
    lesson_dict = lesson_data.model_dump()
    
    # Validar que la lección tenga al menos un ejercicio
    validate_module_lessons([lesson_dict])

    # 3. Generar IDs para la nueva lección
    lesson_dict["_id"] = ObjectId()
    lesson_dict["module_id"] = module_obj_id

    # 4. Agregar la lección al array de lecciones
    result = await modules_collection.update_one(
        {"_id": module_obj_id},
        {"$push": {"lessons": lesson_dict}}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add lesson to module."
        )

    # 5. Obtener el módulo actualizado
    updated_module = await modules_collection.find_one({"_id": module_obj_id})
    
    cleaned_module_dict = convert_object_ids_to_str(updated_module)
    return ModuleOut.model_validate(cleaned_module_dict)

# ADD EXERCISE -> Agregar un nuevo ejercicio a una lección existente
async def add_exercise_to_lesson_service(module_id: str, lesson_id: str, exercise_data: dict) -> Optional[ModuleOut]:
    """
    Agrega un nuevo ejercicio a una lección específica dentro de un módulo.
    Valida que el ejercicio tenga los campos requeridos según su tipo.
    """
    try:
        module_obj_id = ObjectId(module_id)
        lesson_obj_id = ObjectId(lesson_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid module or lesson ID format.")

    # 1. Verificar que el módulo existe
    existing_module = await modules_collection.find_one({"_id": module_obj_id})
    if not existing_module:
        return None  # Módulo no encontrado

    # 2. Buscar la lección dentro del módulo
    lesson_found = False
    lesson_index = None
    for idx, lesson in enumerate(existing_module.get("lessons", [])):
        if str(lesson.get("_id")) == lesson_id:
            lesson_found = True
            lesson_index = idx
            break

    if not lesson_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lección con ID {lesson_id} no encontrada en el módulo."
        )

    # 3. Validar el ejercicio
    validate_exercise_fields(
        exercise_data,
        exercise_data.get("type"),
        exercise_data.get("title", "Nuevo ejercicio"),
        existing_module["lessons"][lesson_index].get("title", f"Lección #{lesson_index + 1}")
    )

    # 4. Generar UUID para el ejercicio si no existe
    if "exercise_uuid" not in exercise_data:
        import uuid
        exercise_data["exercise_uuid"] = str(uuid.uuid4())

    # 5. Agregar el ejercicio al array de ejercicios de la lección
    result = await modules_collection.update_one(
        {
            "_id": module_obj_id,
            f"lessons.{lesson_index}._id": lesson_obj_id
        },
        {"$push": {f"lessons.{lesson_index}.exercises": exercise_data}}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add exercise to lesson."
        )

    # 6. Obtener el módulo actualizado
    updated_module = await modules_collection.find_one({"_id": module_obj_id})
    
    cleaned_module_dict = convert_object_ids_to_str(updated_module)
    return ModuleOut.model_validate(cleaned_module_dict)

# DELETE EXERCISE -> Eliminar un ejercicio de una lección existente
async def delete_exercise_from_lesson_service(module_id: str, lesson_id: str, exercise_uuid: str) -> Optional[ModuleOut]:
    """
    Elimina un ejercicio específico de una lección dentro de un módulo.
    """
    try:
        module_obj_id = ObjectId(module_id)
        lesson_obj_id = ObjectId(lesson_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid module or lesson ID format.")

    # 1. Verificar que el módulo existe
    existing_module = await modules_collection.find_one({"_id": module_obj_id})
    if not existing_module:
        return None  # Módulo no encontrado

    # 2. Buscar la lección dentro del módulo
    lesson_found = False
    lesson_index = None
    for idx, lesson in enumerate(existing_module.get("lessons", [])):
        if str(lesson.get("_id")) == lesson_id:
            lesson_found = True
            lesson_index = idx
            break

    if not lesson_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lección con ID {lesson_id} no encontrada en el módulo."
        )

    # 3. Eliminar el ejercicio usando $pull
    result = await modules_collection.update_one(
        {
            "_id": module_obj_id,
            f"lessons.{lesson_index}._id": lesson_obj_id
        },
        {"$pull": {f"lessons.{lesson_index}.exercises": {"exercise_uuid": exercise_uuid}}}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejercicio con UUID {exercise_uuid} no encontrado en la lección."
        )

    # 4. Obtener el módulo actualizado
    updated_module = await modules_collection.find_one({"_id": module_obj_id})
    
    cleaned_module_dict = convert_object_ids_to_str(updated_module)
    return ModuleOut.model_validate(cleaned_module_dict)

# UPDATE EXERCISE -> Actualizar un ejercicio en una lección existente
async def update_lesson_in_module_service(module_id: str, lesson_id: str, lesson_data: dict) -> Optional[ModuleOut]:
    """
    Actualiza los metadatos de una lección específica dentro de un módulo.
    Solo actualiza: title, description, xp_reward, is_private, order.
    No modifica la lista de ejercicios.
    """
    try:
        module_obj_id = ObjectId(module_id)
        lesson_obj_id = ObjectId(lesson_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid module or lesson ID format.")

    # 1. Verificar que el módulo existe
    existing_module = await modules_collection.find_one({"_id": module_obj_id})
    if not existing_module:
        return None  # Módulo no encontrado

    # 2. Buscar la lección dentro del módulo
    lesson_found = False
    lesson_index = None
    for idx, lesson in enumerate(existing_module.get("lessons", [])):
        if str(lesson.get("_id")) == lesson_id:
            lesson_found = True
            lesson_index = idx
            break

    if not lesson_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lección con ID {lesson_id} no encontrada en el módulo."
        )

    # 3. Preparar campos a actualizar (solo metadata)
    update_fields = {}
    if "title" in lesson_data and lesson_data["title"]:
        update_fields[f"lessons.{lesson_index}.title"] = lesson_data["title"]
    if "description" in lesson_data and lesson_data["description"] is not None:
        update_fields[f"lessons.{lesson_index}.description"] = lesson_data["description"]
    if "xp_reward" in lesson_data and lesson_data["xp_reward"] is not None:
        update_fields[f"lessons.{lesson_index}.xp_reward"] = lesson_data["xp_reward"]
    if "is_private" in lesson_data and lesson_data["is_private"] is not None:
        update_fields[f"lessons.{lesson_index}.is_private"] = lesson_data["is_private"]
    if "order" in lesson_data and lesson_data["order"] is not None:
        update_fields[f"lessons.{lesson_index}.order"] = lesson_data["order"]

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay campos válidos para actualizar."
        )

    # 4. Actualizar la lección
    result = await modules_collection.update_one(
        {"_id": module_obj_id},
        {"$set": update_fields}
    )

    if result.modified_count == 0:
        # Puede ser que los datos sean idénticos
        pass

    # 5. Obtener el módulo actualizado
    updated_module = await modules_collection.find_one({"_id": module_obj_id})
    
    cleaned_module_dict = convert_object_ids_to_str(updated_module)
    return ModuleOut.model_validate(cleaned_module_dict)


async def update_exercise_in_lesson_service(module_id: str, lesson_id: str, exercise_uuid: str, exercise_data: dict) -> Optional[ModuleOut]:
    """
    Actualiza un ejercicio específico de una lección dentro de un módulo.
    """
    try:
        module_obj_id = ObjectId(module_id)
        lesson_obj_id = ObjectId(lesson_id)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid module or lesson ID format.")

    # 1. Verificar que el módulo existe
    existing_module = await modules_collection.find_one({"_id": module_obj_id})
    if not existing_module:
        return None  # Módulo no encontrado

    # 2. Buscar la lección dentro del módulo
    lesson_found = False
    lesson_index = None
    for idx, lesson in enumerate(existing_module.get("lessons", [])):
        if str(lesson.get("_id")) == lesson_id:
            lesson_found = True
            lesson_index = idx
            break

    if not lesson_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lección con ID {lesson_id} no encontrada en el módulo."
        )

    # 3. Validar el ejercicio actualizado
    validate_exercise_fields(
        exercise_data,
        exercise_data.get("type"),
        exercise_data.get("title", "Ejercicio editado"),
        existing_module["lessons"][lesson_index].get("title", f"Lección #{lesson_index + 1}")
    )

    # 4. Actualizar el ejercicio usando arrayFilters
    result = await modules_collection.update_one(
        {
            "_id": module_obj_id,
            f"lessons.{lesson_index}._id": lesson_obj_id
        },
        {"$set": {f"lessons.{lesson_index}.exercises.$[ex]": exercise_data}},
        array_filters=[{"ex.exercise_uuid": exercise_uuid}]
    )

    if result.modified_count == 0:
        # Verificar si el ejercicio existe
        lesson = existing_module["lessons"][lesson_index]
        exercise_exists = any(ex.get("exercise_uuid") == exercise_uuid for ex in lesson.get("exercises", []))
        
        if not exercise_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ejercicio con UUID {exercise_uuid} no encontrado en la lección."
            )
        # Si existe pero no se modificó, puede ser porque los datos son idénticos
        
    # 5. Obtener el módulo actualizado
    updated_module = await modules_collection.find_one({"_id": module_obj_id})
    
    cleaned_module_dict = convert_object_ids_to_str(updated_module)
    return ModuleOut.model_validate(cleaned_module_dict)