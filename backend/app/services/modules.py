from typing import Optional, List, Any
from bson import ObjectId
from fastapi import HTTPException, status

from schemas.modules import ModuleCreate, ModuleUpdate, ModuleOut
from schemas.lessons import LessonCreate, LessonUpdate, LessonOut
from db.db import modules_collection
from services.lessons import create_lesson_service, update_lesson_service, get_lesson_by_id_service

# Función auxiliar para convertir ObjectIds a strings recursivamente
def convert_object_ids_to_str(obj: Any) -> Any:
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, list):
        return [convert_object_ids_to_str(item) for item in obj]
    if isinstance(obj, dict):
        return {key: convert_object_ids_to_str(value) for key, value in obj.items()}
    return obj

# CREATE -> Crear un modulo con lecciones y ejercicios incrustados
async def create_module_service(module_data: ModuleCreate) -> ModuleOut:
    """
    Crea un nuevo modulo con lecciones y ejercicios incrustados,
    generando los ObjectIds de las lecciones antes de la inserción.
    """
    module_dict = module_data.model_dump()
    
    # 1. Generar el ObjectId para el modulo (lo usaremos para el module_id en las lecciones)
    module_id = ObjectId()
    module_dict["_id"] = module_id
    
    # 2. Generar IDs para cada lección incrustada
    for lesson in module_dict.get("lessons", []):
        # Asigna un _id único a la lección incrustada (necesario para la validación de LessonOut)
        lesson["_id"] = ObjectId() 
        # Inyecta el ID del modulo en la lección incrustada (para coherencia)
        lesson["module_id"] = module_id
    
    # 3. Insertar el documento completo
    result = await modules_collection.insert_one(module_dict)
    
    # 4. Obtener y limpiar para la salida
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

    # 3. Fusionar los datos existentes con los nuevos
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
            if not lesson_data.get("_id"):
                lesson_data["_id"] = ObjectId()
                lesson_data["module_id"] = module_obj_id
        merged_data["lessons"] = lessons_list
        
    # 4. Reemplazar el documento completo en la base de datos
    await modules_collection.replace_one(
        {"_id": module_obj_id},
        merged_data
    )
    
    # 5. Obtener el documento final y retornarlo
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