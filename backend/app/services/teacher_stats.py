# backend/app/services/teacher_stats.py
"""
Servicio para generar estadísticas agregadas de todos los alumnos.
Solo accesible para profesores.
"""

from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId


async def get_all_students_stats(db: AsyncIOMotorDatabase) -> List[Dict[str, Any]]:
    """
    Obtiene estadísticas de TODOS los estudiantes.
    
    Retorna:
        Lista de diccionarios con:
        - user_id, username, email, role
        - total_xp: Puntos totales acumulados
        - streak_days: Días consecutivos de práctica
        - lessons_completed: Número de lecciones completadas
        - exercises_completed: Número de ejercicios completados
        - last_activity: Fecha de última actividad
        - active_days: Lista de fechas únicas en que practicó
        - modules_progress: Progreso por módulo
    """
    
    # 1. Obtener todos los usuarios con rol 'student'
    students = await db["users"].find({"role": "student"}).to_list(length=None)
    
    stats_list = []
    
    for student in students:
        user_id = str(student["_id"])
        
        # 2. Obtener progreso de lecciones del estudiante
        lesson_progress = await db["lesson_progress"].find({"user_id": user_id}).to_list(length=None)
        
        # 3. Obtener sesiones del estudiante (para días activos)
        sessions = await db["sessions"].find({"user_id": user_id}).to_list(length=None)
        
        # 4. Calcular estadísticas
        total_xp = student.get("total_points", 0)
        streak_days = student.get("streak", {}).get("current_days", 0)
        
        # ✅ Lecciones completadas (usando is_completed)
        lessons_completed = sum(1 for lp in lesson_progress if lp.get("is_completed", False))
        
        # ✅ Ejercicios completados (únicos por UUID)
        completed_exercise_uuids = set()
        for lp in lesson_progress:
            for ex in lp.get("exercises", []):
                # ✅ CAMPO CORRECTO: is_correct
                if ex.get("is_correct", False):
                    completed_exercise_uuids.add(ex.get("exercise_uuid"))
        exercises_completed = len(completed_exercise_uuids)
        
        # Última actividad
        last_activity = None
        if lesson_progress:
            latest = max(lesson_progress, key=lambda x: x.get("last_attempt", datetime.min))
            last_activity = latest.get("last_attempt")
        
        # Días activos (fechas únicas de sesiones)
        active_days = []
        if sessions:
            unique_dates = set()
            for session in sessions:
                start_time = session.get("start_time")
                if start_time:
                    # Convertir a fecha (sin hora)
                    date_only = start_time.date() if isinstance(start_time, datetime) else start_time
                    unique_dates.add(str(date_only))
            active_days = sorted(list(unique_dates), reverse=True)
        
        # Calcular progreso global (lecciones completadas / total lecciones)
        all_modules = await db["modules"].find().to_list(length=None)
        total_lessons_in_system = sum(len(m.get("lessons", [])) for m in all_modules)
        global_progress_percentage = 0
        if total_lessons_in_system > 0:
            global_progress_percentage = (lessons_completed / total_lessons_in_system) * 100
        
        # Progreso por módulo con detalles
        modules_progress = {}
        for lp in lesson_progress:
            module_id = lp.get("module_id")
            if module_id not in modules_progress:
                modules_progress[module_id] = {
                    "lessons_completed": 0,
                    "total_lessons": 0,
                    "total_score": 0,
                    "best_scores": []
                }
            
            if lp.get("is_completed", False):
                modules_progress[module_id]["lessons_completed"] += 1
            
            modules_progress[module_id]["total_score"] += lp.get("best_score", 0)
            modules_progress[module_id]["best_scores"].append({
                "lesson_id": lp.get("lesson_id"),
                "score": lp.get("best_score", 0),
                "total_possible": lp.get("total_possible", 0)
            })
        
        # Agregar total_lessons a cada módulo
        for module in all_modules:
            module_id = str(module["_id"])
            if module_id in modules_progress:
                modules_progress[module_id]["total_lessons"] = len(module.get("lessons", []))
        
        # 5. Construir objeto de estadísticas
        stats_list.append({
            "user_id": user_id,
            "username": student.get("username", "Unknown"),
            "email": student.get("email", ""),
            "total_xp": total_xp,
            "streak_days": streak_days,
            "lessons_completed": lessons_completed,
            "exercises_completed": exercises_completed,
            "global_progress_percentage": round(global_progress_percentage, 1),
            "global_progress_text": f"{lessons_completed}/{total_lessons_in_system} lecciones",
            "last_activity": last_activity.isoformat() if last_activity else None,
            "active_days": active_days,
            "active_days_count": len(active_days),
            "modules_progress": modules_progress
        })
    
    # Ordenar por XP total (mayor a menor)
    stats_list.sort(key=lambda x: x["total_xp"], reverse=True)
    
    return stats_list


async def get_student_detailed_progress(
    db: AsyncIOMotorDatabase, 
    student_id: str
) -> Dict[str, Any]:
    """
    Obtiene el progreso DETALLADO de un estudiante específico.
    Incluye información por módulo, lección y ejercicio.
    
    Args:
        db: Base de datos
        student_id: ID del estudiante
    
    Returns:
        Diccionario con progreso detallado organizado por módulo
    """
    
    # 1. Obtener información del usuario
    try:
        user = await db["users"].find_one({"_id": ObjectId(student_id)})
    except:
        user = await db["users"].find_one({"_id": student_id})
    
    if not user:
        return {"error": "Student not found"}
    
    # 2. Obtener todo el progreso de lecciones
    lesson_progress = await db["lesson_progress"].find(
        {"user_id": student_id}
    ).to_list(length=None)
    
    # 3. Obtener todos los módulos para contexto
    modules = await db["modules"].find().to_list(length=None)
    
    # 4. Organizar progreso por módulo
    detailed_progress = {
        "user_info": {
            "user_id": student_id,
            "username": user.get("username"),
            "email": user.get("email"),
            "total_xp": user.get("total_points", 0),
            "streak_days": user.get("streak", {}).get("current_days", 0)
        },
        "modules": []
    }
    
    for module in modules:
        module_id = str(module["_id"])
        module_data = {
            "module_id": module_id,
            "module_title": module.get("title"),
            "lessons": []
        }
        
        # Buscar progreso de lecciones de este módulo
        for lesson in module.get("lessons", []):
            lesson_id = lesson.get("_id") or lesson.get("lesson_id")
            if not lesson_id:
                continue
            
            lesson_id = str(lesson_id)
            
            # Buscar progreso de esta lección
            lp = next((lp for lp in lesson_progress if lp.get("lesson_id") == lesson_id), None)
            
            lesson_data = {
                "lesson_id": lesson_id,
                "lesson_title": lesson.get("title"),
                "is_completed": lp.get("is_completed", False) if lp else False,
                "best_score": lp.get("best_score", 0) if lp else 0,
                "total_possible": lp.get("total_possible", 0) if lp else 0,
                "attempt_count": lp.get("attempt_count", 0) if lp else 0,
                "last_attempt": lp.get("last_attempt").isoformat() if lp and lp.get("last_attempt") else None,
                "exercises": []
            }
            
            # Agregar información de ejercicios
            if lp:
                for ex_attempt in lp.get("exercises", []):
                    lesson_data["exercises"].append({
                        "exercise_uuid": ex_attempt.get("exercise_uuid"),
                        "is_correct": ex_attempt.get("is_correct", False),
                        "points_earned": ex_attempt.get("points_earned", 0),
                        "attempt_time": ex_attempt.get("attempt_time").isoformat() if ex_attempt.get("attempt_time") else None
                    })
            
            module_data["lessons"].append(lesson_data)
        
        detailed_progress["modules"].append(module_data)
    
    return detailed_progress
