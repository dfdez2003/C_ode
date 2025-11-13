from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from schemas.modules import ModuleCreate, ModuleUpdate, ModuleOut
from services.modules import create_module_service,get_module_by_id_service,update_module_service,delete_module_service
from db.db import modules_collection
from utils.lesson import convert_object_ids_to_str
from utils.user import require_teacher_role

# Ruta del router para módulos
router = APIRouter(prefix="/modules", tags=["Modules"])

# ----------------------> Rutas para la gestión de módulos con lecciones y ejercicios embebidos <---------------------- 

# POST -> Crear un módulo (Solo para profesores)
@router.post("/",response_model=ModuleOut,status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_teacher_role)],summary="Create a new module with embedded lessons and exercises.")
async def create_module_route(module: ModuleCreate):
    created_module = await create_module_service(module)
    if not created_module:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Failed to create module.")
    return created_module

# GET -> Obtener un módulo por ID (Disponible para todos)
@router.get("/{module_id}",response_model=ModuleOut,summary="Get a module by ID, including all lessons and exercises.")
async def read_module_route(module_id: str):
    module = await get_module_by_id_service(module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return module

# GET -> Obtener todos los módulos (Disponible para todos)

@router.get("/",response_model=List[ModuleOut], summary="Get a list of all modules, including their lessons and exercises.")
async def list_modules_route():
    all_modules = await modules_collection.find().to_list(length=None)
    # Convertir ObjectIds a strings para la salida
    cleaned_modules = [convert_object_ids_to_str(m) for m in all_modules]
    return [ModuleOut.model_validate(m) for m in cleaned_modules]

# PUT -> Actualizar un módulo (Solo para profesores)
@router.put("/{module_id}",response_model=ModuleOut,dependencies=[Depends(require_teacher_role)],summary="Update a module's details or embedded lessons.")
async def update_module_route(module_id: str, update_data: ModuleUpdate):
    updated_module = await update_module_service(module_id, update_data)
    if not updated_module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return updated_module

# DELETE -> Eliminar un módulo (Solo para profesores)
@router.delete("/{module_id}",status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(require_teacher_role)],summary="Delete a module and all its embedded lessons.")
async def delete_module_route(module_id: str):
    deleted = await delete_module_service(module_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return None