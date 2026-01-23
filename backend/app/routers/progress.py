# routers/progress.py

from fastapi import APIRouter, Depends, HTTPException, status
from schemas.progress import ProgressResponse, ExerciseSubmission, UserProgressOut, UserProgressSummary
from motor.motor_asyncio import AsyncIOMotorDatabase
from db.db import get_database
from schemas.users import UserResponse
from utils.user import get_current_user, require_teacher_role
from services.progress import register_progress_service, get_user_global_progress_service, get_user_progress_summary
from services.teacher_stats import get_all_students_stats, get_student_detailed_progress
from services.student_stats import get_student_own_stats
from utils.user import get_current_user_from_token
from services.rewards import RewardService
from datetime import datetime, timezone
from typing import Any, List

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.post("/exercise/validate")
async def validate_exercise(
    submission: ExerciseSubmission,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Valida un ejercicio SIN grabar progreso.
    Se usa para el botón "Ejecutar" en make_code que debe mostrar feedback antes de "Continuar".
    
    Retorna el mismo formato que /exercise pero sin modificar la base de datos.
    """
    from services.progress import check_solution
    
    # 1. Buscar el módulo para obtener el ejercicio
    module_doc = await db["modules"].find_one({"_id": submission.module_id})
    if not module_doc:
        raise HTTPException(status_code=404, detail="Module not found")
    
    # 2. Buscar la lección
    lesson = next((l for l in module_doc.get("lessons", []) if l.get("lesson_id") == submission.lesson_id), None)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # 3. Buscar el ejercicio
    exercise = next((e for e in lesson.get("exercises", []) if e.get("uuid") == submission.exercise_uuid), None)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    # 4. Validar la respuesta (sin grabar en DB)
    is_correct, code_feedback = await check_solution(exercise, submission.user_response)
    
    # 5. Retornar solo el resultado de validación
    return {
        "is_correct": is_correct,
        "code_feedback": code_feedback,
        "points": exercise.get("points", 0)
    }


@router.post("/exercise")
async def submit_exercise(
    submission: ExerciseSubmission, 
    db: AsyncIOMotorDatabase = Depends(get_database), 
    current_user: UserResponse = Depends(get_current_user)
):
    # 1. Registrar el progreso del ejercicio
    result = await register_progress_service(db, current_user.id, submission)
    
    # 2. Si la lección terminó, procesar recompensas automáticas
    achievements_earned = []
    xp_bonus = 0
    
    if result.lesson_finished:
        try:
            user_id = str(current_user.id)
            
            # 2A. Recompensas por lección perfecta
            lesson_result = await RewardService.process_lesson_completion(
                db, user_id, submission.lesson_id, submission.module_id
            )
            if lesson_result:
                xp_bonus += lesson_result.get("total_xp_earned", 0)
                achievements_earned.extend(lesson_result.get("perfect_lesson_achievements", []))
            
            # 2B. Recompensas por racha
            streak_result = await RewardService.handle_streak_and_achievements(
                db, user_id, datetime.now(timezone.utc)
            )
            if streak_result:
                achievements_earned.extend(streak_result.get("new_achievements", []))
            
            # 2C. Recompensas por hitos de XP
            user = await db["users"].find_one({"_id": current_user.id})
            if user:
                total_xp = user.get("total_points", 0)
                xp_milestones = await RewardService.process_xp_milestones(db, user_id, total_xp)
                achievements_earned.extend(xp_milestones)
                
        except Exception as e:
            print(f"⚠️  Error procesando recompensas: {e}")
            # No fallar la respuesta si hay error en recompensas
            
    return {
        "is_correct": result.is_correct,
        "lesson_finished": result.lesson_finished,
        "points_earned": result.points_earned,
        "current_score": result.current_score,
        "total_possible": result.total_possible,
        "code_feedback": result.code_feedback,
        "xp_bonus": xp_bonus,
        "achievements_earned": achievements_earned
    }


# ------------------------------------------------------------------
# GET /progress/user/{user_id} -> Obtener Progreso Global
# ------------------------------------------------------------------
@router.get(
    "/user/{user_id}",
    response_model=List[UserProgressOut],
    summary="Get all progress records for a user."
)
async def get_user_progress_route(
    user_id: str,
    # Aseguramos que solo el usuario logueado o un admin pueda ver su progreso
    current_user: Any = Depends(get_current_user_from_token),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Retrieves the complete list of progress records (one per exercise attempted)
    for the specified user.
    """
    # ⚠️ REGLA DE SEGURIDAD: Solo puedes ver tu propio progreso o si eres un profesor
    if current_user.id != user_id and current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's progress."
        )

    progress_list = await get_user_global_progress_service(db, user_id)
    return progress_list


@router.get("/lesson/{lesson_id}/status", status_code=status.HTTP_200_OK)
async def get_lesson_status(
    lesson_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Verifica el estado de una lección para el usuario actual.
    Retorna si está bloqueada, el mejor puntaje, número de intentos, etc.
    """
    lesson_progress = await db["lesson_progress"].find_one({
        "user_id": current_user.id,
        "lesson_id": lesson_id
    })
    
    if not lesson_progress:
        # Primera vez que ve esta lección
        return {
            "is_locked": False,
            "is_completed": False,
            "best_score": 0,
            "attempt_count": 0,
            "can_attempt": True
        }
    
    is_locked = lesson_progress.get("is_locked", False)
    
    return {
        "is_locked": is_locked,
        "is_completed": lesson_progress.get("is_completed", False),
        "best_score": lesson_progress.get("best_score", 0),
        "attempt_count": lesson_progress.get("attempt_count", 0),
        "can_attempt": not is_locked
    }


@router.get("/user/{user_id}", response_model=UserProgressSummary, status_code=status.HTTP_200_OK)
async def get_progress_for_user(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user) # Usa el JWT para saber quién pide el progreso
):
    """
    Retorna el resumen de progreso (puntos, racha, ejercicios completados) de un usuario.
    Nota: En un entorno de producción, se verificaría que user_id coincida con current_user.id
    a menos que el usuario actual sea un profesor/administrador.
    """
    # ✨ (Opcional) Seguridad: Asegurar que el usuario solo pueda ver su propio progreso
    if current_user.role == "student" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver el progreso de otros usuarios."
        )

    try:
        summary = await get_user_progress_summary(db=db, user_id=user_id)
        return summary
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener el progreso: {str(e)}"
        )
# ========== ENDPOINTS PARA PROFESORES ==========

@router.get("/stats/all-students", dependencies=[Depends(require_teacher_role)])
async def get_all_students_statistics(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtiene estadísticas agregadas de TODOS los estudiantes.
    Solo accesible para profesores.
    
    Retorna:
        - Lista de estudiantes con sus estadísticas:
          - XP total, racha, lecciones/ejercicios completados
          - Días activos, última actividad
          - Progreso por módulo
    """
    try:
        stats = await get_all_students_stats(db)
        return {
            "total_students": len(stats),
            "students": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/stats/student/{student_id}", dependencies=[Depends(require_teacher_role)])
async def get_student_detailed_statistics(
    student_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtiene el progreso DETALLADO de un estudiante específico.
    Solo accesible para profesores.
    
    Incluye:
        - Información del usuario
        - Progreso por módulo, lección y ejercicio
        - Historial de intentos
    """
    try:
        detailed_progress = await get_student_detailed_progress(db, student_id)
        
        if "error" in detailed_progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detailed_progress["error"]
            )
        
        return detailed_progress
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener progreso detallado: {str(e)}"
        )



# ========== ENDPOINT PARA ESTUDIANTES ==========

@router.get("/stats/my-stats")
async def get_my_statistics(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtiene las estadísticas personales del estudiante actual.
    Incluye gamificación, badges, nivel, progreso detallado y mensajes motivacionales.
    
    Accesible para cualquier usuario autenticado (estudiantes).
    """
    try:
        stats = await get_student_own_stats(db, current_user.id)
        
        if "error" in stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=stats["error"]
            )
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas personales: {str(e)}"
        )

