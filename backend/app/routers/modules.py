from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from schemas.modules import ModuleCreate, ModuleUpdate, ModuleOut
from schemas.lessons import LessonCreate
from services.modules import create_module_service,get_module_by_id_service,update_module_service,delete_module_service,add_lesson_to_module_service,add_exercise_to_lesson_service,delete_exercise_from_lesson_service,update_exercise_in_lesson_service,update_lesson_in_module_service
from services.module_metadata import update_module_metadata_service
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

# PATCH -> Actualizar metadatos del módulo (title, description, order, estimate_time) sin tocar lecciones
@router.patch("/{module_id}",response_model=ModuleOut,dependencies=[Depends(require_teacher_role)],summary="Update module metadata (title, description, order, estimate_time) without modifying lessons.")
async def update_module_metadata_route(module_id: str, metadata: dict):
    updated_module = await update_module_metadata_service(module_id, metadata)
    if not updated_module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return updated_module

# PATCH -> Agregar una nueva lección a un módulo existente (Solo para profesores)
@router.patch("/{module_id}/lessons",response_model=ModuleOut,dependencies=[Depends(require_teacher_role)],summary="Add a new lesson with exercises to an existing module.")
async def add_lesson_to_module_route(module_id: str, lesson: LessonCreate):
    updated_module = await add_lesson_to_module_service(module_id, lesson)
    if not updated_module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return updated_module

# PATCH -> Actualizar una lección existente (Solo para profesores)
@router.patch("/{module_id}/lessons/{lesson_id}",response_model=ModuleOut,dependencies=[Depends(require_teacher_role)],summary="Update lesson metadata (title, description, xp_reward, is_private, order).")
async def update_lesson_in_module_route(module_id: str, lesson_id: str, lesson: dict):
    updated_module = await update_lesson_in_module_service(module_id, lesson_id, lesson)
    if not updated_module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return updated_module

# PATCH -> Agregar un nuevo ejercicio a una lección existente (Solo para profesores)
@router.patch("/{module_id}/lessons/{lesson_id}/exercises",response_model=ModuleOut,dependencies=[Depends(require_teacher_role)],summary="Add a new exercise to an existing lesson.")
async def add_exercise_to_lesson_route(module_id: str, lesson_id: str, exercise: dict):
    updated_module = await add_exercise_to_lesson_service(module_id, lesson_id, exercise)
    if not updated_module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return updated_module

# DELETE -> Eliminar un ejercicio de una lección existente (Solo para profesores)
@router.delete("/{module_id}/lessons/{lesson_id}/exercises/{exercise_uuid}",response_model=ModuleOut,dependencies=[Depends(require_teacher_role)],summary="Delete an exercise from an existing lesson.")
async def delete_exercise_from_lesson_route(module_id: str, lesson_id: str, exercise_uuid: str):
    updated_module = await delete_exercise_from_lesson_service(module_id, lesson_id, exercise_uuid)
    if not updated_module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return updated_module

# PATCH -> Actualizar un ejercicio en una lección existente (Solo para profesores)
@router.patch("/{module_id}/lessons/{lesson_id}/exercises/{exercise_uuid}",response_model=ModuleOut,dependencies=[Depends(require_teacher_role)],summary="Update an exercise in an existing lesson.")
async def update_exercise_in_lesson_route(module_id: str, lesson_id: str, exercise_uuid: str, exercise: dict):
    updated_module = await update_exercise_in_lesson_service(module_id, lesson_id, exercise_uuid, exercise)
    if not updated_module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return updated_module