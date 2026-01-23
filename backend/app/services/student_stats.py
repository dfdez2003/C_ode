# backend/app/services/student_stats.py

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Dict, Any, List
from datetime import datetime, timedelta

async def get_student_own_stats(db: AsyncIOMotorDatabase, student_id: str) -> Dict[str, Any]:
    """
    Obtiene las estadísticas personales de un estudiante para su dashboard.
    Incluye gamificación, logros, y datos motivacionales.
    """
    
    # 1. Obtener información del usuario
    user = await db["users"].find_one({"_id": ObjectId(student_id)})
    if not user:
        return {"error": "Usuario no encontrado"}
    
    # 2. Obtener todo el progreso de lecciones
    lesson_progress = await db["lesson_progress"].find({"user_id": student_id}).to_list(length=None)
    
    # 3. Obtener todas las sesiones del estudiante
    sessions = await db["sessions"].find({"user_id": student_id}).to_list(length=None)
    
    # 4. Calcular estadísticas básicas
    total_xp = user.get("total_points", 0)
    streak_days = user.get("streak_days", 0)
    
    # Contar lecciones y ejercicios completados
    lessons_completed = 0
    exercises_completed = 0
    total_exercises_attempted = 0
    perfect_scores = 0  # Lecciones con puntaje perfecto
    
    for lp in lesson_progress:
        # ✅ CAMPO CORRECTO: is_completed (no "completed")
        if lp.get("is_completed", False):
            lessons_completed += 1
            
            # Verificar si es puntaje perfecto (best_score == total_possible)
            if lp.get("best_score", 0) == lp.get("total_possible", 0) and lp.get("total_possible", 0) > 0:
                perfect_scores += 1
        
        # ✅ CONTAR EJERCICIOS: Los ejercicios solo se registran si se intentan
        exercises = lp.get("exercises", [])
        
        # Crear set de UUIDs únicos correctos
        unique_correct_uuids = set()
        for ex in exercises:
            # ✅ CAMPO CORRECTO: is_correct (no "completed")
            if ex.get("is_correct", False):
                unique_correct_uuids.add(ex.get("exercise_uuid"))
        
        exercises_completed += len(unique_correct_uuids)
        total_exercises_attempted += len(exercises)
    
    # 5. Calcular días activos y actividad reciente
    active_days = set()
    for session in sessions:
        date_str = session.get("date", "")
        if date_str:
            date_only = date_str.split("T")[0]
            active_days.add(date_only)
    
    active_days_list = sorted(list(active_days), reverse=True)
    active_days_count = len(active_days_list)
    
    # 6. Obtener última actividad
    last_activity = None
    if sessions:
        last_session = max(sessions, key=lambda s: s.get("date", ""))
        last_activity = last_session.get("date")
    
    # 7. Calcular nivel basado en XP (cada 500 XP = 1 nivel)
    level = (total_xp // 500) + 1
    xp_for_current_level = (level - 1) * 500
    xp_for_next_level = level * 500
    xp_progress_in_level = total_xp - xp_for_current_level
    xp_needed_for_next = xp_for_next_level - total_xp
    level_progress_percentage = (xp_progress_in_level / 500) * 100
    
    # 7.5. Calcular progreso global (lecciones completadas / total lecciones)
    total_lessons_in_system = 0
    for module in await db["modules"].find().to_list(length=None):
        total_lessons_in_system += len(module.get("lessons", []))
    
    global_progress_percentage = 0
    if total_lessons_in_system > 0:
        global_progress_percentage = (lessons_completed / total_lessons_in_system) * 100
    
    # 8. Obtener progreso por módulo
    modules = await db["modules"].find().sort("order", 1).to_list(length=None)
    modules_progress = []
    
    for module in modules:
        module_id = str(module["_id"])
        
        # Obtener lecciones del módulo
        module_lessons = module.get("lessons", [])
        
        module_completed_lessons = 0
        module_total_exercises = 0
        module_completed_exercises = 0
        module_score_sum = 0
        lessons_details = []  # Detalles de CADA lección para solo lectura
        
        for lesson in module_lessons:
            lesson_id = str(lesson["_id"])
            
            # Buscar progreso de esta lección
            lp = next((l for l in lesson_progress if l.get("lesson_id") == lesson_id), None)
            
            lesson_detail = {
                "lesson_id": lesson_id,
                "lesson_title": lesson.get("title", "Sin título"),
                "status": "completed" if (lp and lp.get("is_completed", False)) else "not_started",
                "score": lp.get("best_score", 0) if lp else 0,
                "total_possible": lp.get("total_possible", 0) if lp else 0,
                "attempt_count": lp.get("attempt_count", 0) if lp else 0
            }
            lessons_details.append(lesson_detail)
            
            if lp:
                # ✅ CAMPO CORRECTO: is_completed
                if lp.get("is_completed", False):
                    module_completed_lessons += 1
                
                exercises = lp.get("exercises", [])
                lesson_exercises_count = len(lesson.get("exercises", []))  # Total real de ejercicios en la lección
                module_total_exercises += lesson_exercises_count
                
                # Contar ejercicios correctos únicos
                unique_correct = set()
                for ex in exercises:
                    # ✅ CAMPO CORRECTO: is_correct
                    if ex.get("is_correct", False):
                        unique_correct.add(ex.get("exercise_uuid"))
                
                module_completed_exercises += len(unique_correct)
                
                # Usar best_score para el promedio
                best_score = lp.get("best_score", 0)
                total_possible = lp.get("total_possible", 1)
                lesson_percentage = (best_score / total_possible * 100) if total_possible > 0 else 0
                module_score_sum += lesson_percentage
        
        # Calcular porcentaje de progreso del módulo
        total_lessons = len(module_lessons)
        module_progress_percentage = 0
        if total_lessons > 0:
            module_progress_percentage = (module_completed_lessons / total_lessons) * 100
        
        # Promedio de score en LECCIONES del módulo (no ejercicios)
        avg_score = 0
        lessons_with_progress = sum(1 for lesson in module_lessons 
                                   if any(lp.get("lesson_id") == str(lesson["_id"]) for lp in lesson_progress))
        if lessons_with_progress > 0:
            avg_score = module_score_sum / lessons_with_progress
        
        modules_progress.append({
            "module_id": module_id,
            "module_title": module.get("title", "Sin título"),
            "total_lessons": total_lessons,
            "completed_lessons": module_completed_lessons,
            "progress_text": f"{module_completed_lessons}/{total_lessons}",
            "total_exercises": module_total_exercises,
            "completed_exercises": module_completed_exercises,
            "progress_percentage": round(module_progress_percentage, 1),
            "average_score": round(avg_score, 1),
            "status": "completed" if module_completed_lessons == total_lessons and total_lessons > 0 else "in_progress" if module_completed_lessons > 0 else "not_started",
            "lessons": lessons_details  # 📌 Detalles de lecciones para solo lectura
        })
    
    # 9. Calcular logros (badges)
    badges = []
    
    # Badge: Primera lección
    if lessons_completed >= 1:
        badges.append({
            "id": "first_lesson",
            "name": "Primer Paso",
            "description": "Completaste tu primera lección",
            "icon": "🎯",
            "unlocked": True
        })
    
    # Badge: 5 lecciones
    if lessons_completed >= 5:
        badges.append({
            "id": "5_lessons",
            "name": "Aprendiz",
            "description": "Completaste 5 lecciones",
            "icon": "📚",
            "unlocked": True
        })
    
    # Badge: 10 lecciones
    if lessons_completed >= 10:
        badges.append({
            "id": "10_lessons",
            "name": "Estudiante Dedicado",
            "description": "Completaste 10 lecciones",
            "icon": "🎓",
            "unlocked": True
        })
    
    # Badge: Racha de 7 días
    if streak_days >= 7:
        badges.append({
            "id": "week_streak",
            "name": "Semana Completa",
            "description": "Racha de 7 días consecutivos",
            "icon": "🔥",
            "unlocked": True
        })
    
    # Badge: Racha de 30 días
    if streak_days >= 30:
        badges.append({
            "id": "month_streak",
            "name": "Imparable",
            "description": "Racha de 30 días consecutivos",
            "icon": "💪",
            "unlocked": True
        })
    
    # Badge: 10 ejercicios perfectos
    if perfect_scores >= 10:
        badges.append({
            "id": "perfectionist",
            "name": "Perfeccionista",
            "description": "10 ejercicios con puntuación perfecta",
            "icon": "⭐",
            "unlocked": True
        })
    
    # Badge: 1000 XP
    if total_xp >= 1000:
        badges.append({
            "id": "xp_1000",
            "name": "Coleccionista de XP",
            "description": "Alcanzaste 1000 XP",
            "icon": "💎",
            "unlocked": True
        })
    
    # Badge: Nivel 5
    if level >= 5:
        badges.append({
            "id": "level_5",
            "name": "Experto",
            "description": "Alcanzaste el nivel 5",
            "icon": "👑",
            "unlocked": True
        })
    
    # 10. Actividad de últimos 30 días (para calendario)
    today = datetime.now()
    last_30_days = []
    
    for i in range(30):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        # Verificar si hubo actividad ese día
        was_active = date_str in active_days
        
        # Contar ejercicios resueltos ese día
        exercises_that_day = 0
        for session in sessions:
            session_date = session.get("date", "")
            if session_date.startswith(date_str):
                exercises_that_day += session.get("exercises_solved", 0)
        
        last_30_days.append({
            "date": date_str,
            "active": was_active,
            "exercises_count": exercises_that_day
        })
    
    last_30_days.reverse()  # Ordenar del más antiguo al más reciente
    
    # 11. Mensaje motivacional basado en progreso
    motivational_message = get_motivational_message(
        total_xp, streak_days, lessons_completed, exercises_completed
    )
    
    # 12. Siguiente meta sugerida
    next_goal = get_next_goal(
        total_xp, streak_days, lessons_completed, exercises_completed, modules_progress
    )
    
    return {
        "user_info": {
            "username": user.get("username"),
            "email": user.get("email"),
            "role": user.get("role")
        },
        "stats": {
            "total_xp": total_xp,
            "level": level,
            "level_progress_percentage": round(level_progress_percentage, 1),
            "xp_for_next_level": xp_needed_for_next,
            "streak_days": streak_days,
            "lessons_completed": lessons_completed,
            "exercises_completed": exercises_completed,
            "exercises_attempted": total_exercises_attempted,
            "perfect_scores": perfect_scores,
            "active_days_count": active_days_count,
            "last_activity": last_activity
        },
        "global_progress_percentage": round(global_progress_percentage, 1),
        "global_progress_text": f"{lessons_completed}/{total_lessons_in_system} lecciones",
        "modules_progress": modules_progress,
        "badges": badges,
        "activity_calendar": last_30_days,
        "motivational_message": motivational_message,
        "next_goal": next_goal
    }


def get_motivational_message(xp: int, streak: int, lessons: int, exercises: int) -> str:
    """Genera un mensaje motivacional basado en el progreso del estudiante"""
    
    if streak >= 30:
        return "¡Increíble! Tu dedicación es inspiradora. ¡Sigue así! 🌟"
    elif streak >= 7:
        return "¡Excelente racha! Mantén el ritmo, vas muy bien. 🔥"
    elif lessons >= 20:
        return "¡Wow! Has completado muchas lecciones. ¡Eres imparable! 🚀"
    elif exercises >= 50:
        return "¡Impresionante! Has resuelto muchos ejercicios. 💪"
    elif xp >= 2000:
        return "¡Tu XP está por las nubes! Eres todo un experto. 👑"
    elif lessons >= 5:
        return "¡Buen progreso! Estás construyendo bases sólidas. 📚"
    elif exercises >= 10:
        return "¡Vas por buen camino! Cada ejercicio te hace mejor. ⭐"
    else:
        return "¡Bienvenido! Cada paso cuenta. ¡Comienza tu aventura! 🎯"


def get_next_goal(xp: int, streak: int, lessons: int, exercises: int, modules: List[Dict]) -> Dict[str, Any]:
    """Sugiere la siguiente meta para el estudiante"""
    
    # Prioridad 1: Racha
    if streak == 0:
        return {
            "type": "streak",
            "title": "Comienza una racha",
            "description": "Practica hoy para iniciar tu racha diaria",
            "icon": "🔥",
            "target": 1
        }
    elif streak < 7:
        return {
            "type": "streak",
            "title": f"Alcanza 7 días de racha",
            "description": f"Te faltan {7 - streak} días para tu badge de semana completa",
            "icon": "🔥",
            "target": 7
        }
    
    # Prioridad 2: Lecciones
    if lessons < 5:
        return {
            "type": "lessons",
            "title": "Completa 5 lecciones",
            "description": f"Te faltan {5 - lessons} lecciones para el badge de Aprendiz",
            "icon": "📚",
            "target": 5
        }
    elif lessons < 10:
        return {
            "type": "lessons",
            "title": "Completa 10 lecciones",
            "description": f"Te faltan {10 - lessons} lecciones para el badge de Estudiante Dedicado",
            "icon": "🎓",
            "target": 10
        }
    
    # Prioridad 3: Módulos sin empezar
    not_started_modules = [m for m in modules if m["status"] == "not_started"]
    if not_started_modules:
        first_module = not_started_modules[0]
        return {
            "type": "module",
            "title": f"Empieza: {first_module['module_title']}",
            "description": "Explora un nuevo módulo y amplía tus conocimientos",
            "icon": "🗺️",
            "target": first_module['module_id']
        }
    
    # Prioridad 4: Módulos en progreso
    in_progress_modules = [m for m in modules if m["status"] == "in_progress"]
    if in_progress_modules:
        first_module = in_progress_modules[0]
        return {
            "type": "module",
            "title": f"Completa: {first_module['module_title']}",
            "description": f"Progreso: {first_module['progress_percentage']}% - ¡Ya casi terminas!",
            "icon": "🎯",
            "target": first_module['module_id']
        }
    
    # Prioridad 5: XP
    next_xp_milestone = ((xp // 500) + 1) * 500
    return {
        "type": "xp",
        "title": f"Alcanza {next_xp_milestone} XP",
        "description": f"Te faltan {next_xp_milestone - xp} XP para subir de nivel",
        "icon": "⭐",
        "target": next_xp_milestone
    }
