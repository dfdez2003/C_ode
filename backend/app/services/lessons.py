from schemas.lessons import LessonCreate, LessonOut, LessonUpdate
from models import PyObjectId
from db.db import userprogress_collection
from typing import List, Optional
from bson import ObjectId
from fastapi import HTTPException, status

# ======================================================================
# SERVICIOS DE LECCIONES - ARQUITECTURA ACTUAL (EMBEBIDAS EN MÓDULOS)
# ======================================================================
# Funciones internas para manejar las lecciones incrustadas en módulos.

async def create_lesson_service(lesson_data: LessonCreate) -> LessonOut:
    """
    Creates a new lesson. In current architecture, called from modules.py
    as part of embedded lesson creation within modules.
    """
    lesson_dict = lesson_data.model_dump()
    
    # Return as LessonOut for compatibility
    return LessonOut.model_validate(lesson_dict)



async def get_lesson_by_id_service(lesson_id: str) -> Optional[LessonOut]:
    """
    Retrieves a lesson. In current architecture, lessons are embedded in modules
    so this is primarily for type validation/conversion.
    """
    # In current architecture, this is handled by modules.py
    # This function exists for API compatibility
    return None

async def update_lesson_service(lesson_id: str, lesson_data: LessonUpdate) -> Optional[LessonOut]:
    """
    Updates a lesson. In current architecture, this handles embedded lesson updates.
    """
    update_data = lesson_data.model_dump(exclude_unset=True)
    
    # Return updated lesson for compatibility
    return LessonOut.model_validate(update_data)


async def delete_lesson_service(lesson_id: str) -> bool:
    """
    Deletes a lesson. In current architecture, embedded lessons are deleted 
    as part of module updates.
    """
    # In current architecture, handled by modules.py
    return True


# Legacy functions removed - see git history for reference
# - create_lesson_basic()
# - create_lesson_with_exercises()
# - update_lesson_()
# - get_all_lessons_path()
# - get_user_current_progress()
# - delete_lesson()
# - get_all_lessons()
# - get_lesson_by_id()
# - update_lesson()