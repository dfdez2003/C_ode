# backend/app/services/module_metadata.py
"""
Servicio para actualizar metadatos de módulos (título, descripción, orden, etc.)
sin tocar las lecciones.
"""

from typing import Optional
from bson import ObjectId
from fastapi import HTTPException, status

from schemas.modules import ModuleOut
from db.db import modules_collection
from services.modules import convert_object_ids_to_str


async def update_module_metadata_service(module_id: str, metadata: dict) -> Optional[ModuleOut]:
    """
    Actualiza solo los metadatos del módulo (title, description, order, estimate_time).
    NO modifica la lista de lecciones.
    
    Args:
        module_id: ID del módulo a actualizar
        metadata: Diccionario con los campos a actualizar (title, description, order, estimate_time)
    
    Returns:
        ModuleOut con los datos actualizados, o None si no se encuentra el módulo
    """
    try:
        module_obj_id = ObjectId(module_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de ID de módulo inválido."
        )
    
    # Verificar que el módulo existe
    existing_module = await modules_collection.find_one({"_id": module_obj_id})
    if not existing_module:
        return None
    
    # Filtrar solo los campos permitidos para evitar modificar lecciones accidentalmente
    allowed_fields = {"title", "description", "order", "estimate_time"}
    update_fields = {k: v for k, v in metadata.items() if k in allowed_fields}
    
    if not update_fields:
        # No hay campos válidos para actualizar
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron campos válidos para actualizar."
        )
    
    # Actualizar solo los metadatos
    result = await modules_collection.update_one(
        {"_id": module_obj_id},
        {"$set": update_fields}
    )
    
    if result.modified_count == 0:
        # Puede ser que los datos sean idénticos
        pass
    
    # Obtener el módulo actualizado
    updated_module = await modules_collection.find_one({"_id": module_obj_id})
    
    cleaned_module_dict = convert_object_ids_to_str(updated_module)
    return ModuleOut.model_validate(cleaned_module_dict)
