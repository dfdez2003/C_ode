from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from bson import ObjectId
from schemas.lessons import LessonCreate, LessonUpdate, LessonOut
from services.lessons import create_lesson_service,get_lesson_by_id_service,update_lesson_service,delete_lesson_service
from utils.user import require_teacher_role

router = APIRouter(prefix="/lessons", tags=["Lessons"])
#--------------------------- Rutas para la gestión de lecciones
# Uso de respaldo ( crud completo en modulos)

# POST -> Crear una lección con ejercicios (Solo para profesores)                                 
@router.post("/",response_model=LessonOut,status_code=status.HTTP_201_CREATED,dependencies=[Depends(require_teacher_role)]) 
async def create_lesson(lesson: LessonCreate):
    created_lesson = await create_lesson_service(lesson)
    if not created_lesson:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Failed to create lesson.")
    return created_lesson

# GET -> Obtener una lección por ID (Disponible para todos)
@router.get("/{lesson_id}", response_model=LessonOut)
async def read_lesson(lesson_id: str):
    lesson = await get_lesson_by_id_service(lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson

# PUT -> Actualizar una lección (Solo para profesores)
@router.put("/{lesson_id}",response_model=LessonOut,dependencies=[Depends(require_teacher_role)])  # 🛡️ Protege la ruta
async def update_lesson_data(lesson_id: str, update_data: LessonUpdate):
    updated_lesson = await update_lesson_service(lesson_id, update_data)
    if not updated_lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return updated_lesson

# DELETE -> Eliminar una lección (Solo para profesores)
@router.delete("/{lesson_id}",status_code=status.HTTP_204_NO_CONTENT,dependencies=[Depends(require_teacher_role)])  # 🛡️ Protege la ruta
async def delete_lesson_data(lesson_id: str):
    deleted = await delete_lesson_service(lesson_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    
    return {"message": "Lesson deleted successfully"}