# backend/app/services/progress.py

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from typing import Any, List, Optional, Dict
from schemas.progress import ExerciseSubmission, UserProgressSummary, LessonProgress, ExerciseAttempt, ProgressResponse
# importamos la función de validación IA
from services.ai_service import ask_llama_validator
# Colecciones
PROGRESS_COLLECTION = "user_progress"
USERS_COLLECTION = "users"
MODULES_COLLECTION = "modules"
SESSIONS_COLLECTION = "sessions"

# =================================================================
# LÓGICA DE VALIDACIÓN DE EJERCICIOS
# =================================================================

# Estos servicios se implementarán en archivos separados 
async def validate_with_ai(question: str, user_answer: str, expected_answer: str) -> bool:
    # Llamada a OpenAI/Anthropic/etc para parafraseo
    return True 

async def run_in_sandbox_and_validate(user_code: str, exercise_data: dict) -> bool:
    # 1. Correr código en contenedor
    # 2. Validar output vs casos de prueba con IA
    return True

# =================================================================
# LÓGICA AUXILIAR DE RASTREO Y PUNTOS
# =================================================================

async def get_exercise_solution(db: AsyncIOMotorDatabase, module_id: str, lesson_id: str, exercise_uuid: str) -> dict:
    """
    Busca la solución completa del ejercicio dentro de la estructura anidada del módulo.
    """
    if not ObjectId.is_valid(module_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de módulo inválido.")

    # Busca el módulo y proyecta solo la lección y ejercicios relevantes
    pipeline = [
        {"$match": {"_id": ObjectId(module_id)}},
        {"$unwind": "$lessons"},
        {"$match": {"lessons._id": ObjectId(lesson_id)}},
        {"$unwind": "$lessons.exercises"},
        {"$match": {"lessons.exercises.exercise_uuid": exercise_uuid}},
        {"$replaceRoot": {"newRoot": "$lessons.exercises"}}
    ]
    
    solution_doc = await db[MODULES_COLLECTION].aggregate(pipeline).to_list(length=1)
    
    if not solution_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ejercicio no encontrado en la lección.")
        
    return solution_doc[0]

# =================================================================
# LÓGICA DE VALIDACIÓN AVANZADA (Estructurada para IA/Sandbox)
# =================================================================

async def check_solution(exercise: dict, user_response: Any) -> tuple[bool, Optional[dict]]:
    """
    Implementa la lógica de validación. 
    Ahora es ASYNC para permitir llamadas a IA y Sandboxes.
    
    Retorna:
        - (bool, dict): (is_correct, feedback)
        - feedback es None para la mayoría de ejercicios
        - feedback tiene estructura detallada para make_code:
          {"code_is_correct": bool, "test_is_correct": bool|None, "has_tests": bool}
    """
    exercise_type = exercise.get("type")
    
    # 1. OPCIÓN MÚLTIPLE (Comparación directa)
    if exercise_type == "question":
        correct = exercise.get("correct_answer")
        user_answer = str(user_response.get("answer", "")).strip() if isinstance(user_response, dict) else str(user_response).strip()
        correct_answer = str(correct).strip()
        
        # Question validation in progress
        
        return (user_answer == correct_answer, None)

    # 2. COMPLETAR (Validación con IA para parafraseo)
    elif exercise_type == "complete":
        expected = exercise.get("correct_answer")
        text = exercise.get("text", "")  # ✅ CORREGIDO: usar "text" en lugar de "description"
        options = exercise.get("options", [])
        
        system_p = "Eres un evaluador de respuestas cortas para un curso de C. Determina si la respuesta del usuario es correcta comparada con la esperada, se estricto pero justo."
        user_p = f"Texto: {text}\nOpciones: {', '.join(options)}\nRespuesta esperada: {expected}\nRespuesta del alumno: {user_response}\n¿Es correcto? Responde solo con SI o NO."
        
        res = await ask_llama_validator(system_p, user_p)
        return ("SI" in res.upper(), None)

    # 3. MAKE CODE (Sandbox + IA) - ✅ RETORNA FEEDBACK DETALLADO
    elif exercise_type == "make_code":
        description = exercise.get("description", "")
        solution = exercise.get("solution", "")
        starter_code = exercise.get("starter_code", "")
        test_cases = exercise.get("test_cases", [])
        has_tests = test_cases and len(test_cases) > 0
        
        # Code exercise validation in progress
        
        # ✅ VALIDACIÓN CRÍTICA: Verificar que el código fue modificado
        user_code_stripped = str(user_response).strip()
        starter_stripped = starter_code.strip()
        
        # Verificar si el código es idéntico al starter_code
        if user_code_stripped == starter_stripped:
            print(f"  ❌ CÓDIGO NO MODIFICADO - Rechazado automáticamente")
            feedback = {
                "code_is_correct": False,
                "test_is_correct": None,
                "has_tests": has_tests,
                "error": "No has modificado el código. Debes completar la solución antes de ejecutar."
            }
            return (False, feedback)
        
        # Verificar si el código está vacío o solo tiene espacios/comentarios
        code_lines = [line.strip() for line in user_code_stripped.split('\n') if line.strip() and not line.strip().startswith('//')]
        if len(code_lines) == 0:
            print(f"  ❌ CÓDIGO VACÍO - Rechazado automáticamente")
            feedback = {
                "code_is_correct": False,
                "test_is_correct": None,
                "has_tests": has_tests,
                "error": "El código está vacío. Escribe tu solución."
            }
            return (False, feedback)
        
        # Verificar que haya una diferencia mínima (al menos 10 caracteres nuevos/cambiados)
        if len(user_code_stripped) < len(starter_stripped) + 10:
            print(f"  ⚠️ CÓDIGO INSUFICIENTEMENTE MODIFICADO")
            feedback = {
                "code_is_correct": False,
                "test_is_correct": None,
                "has_tests": has_tests,
                "error": "El código parece no estar completo. Asegúrate de implementar toda la solución."
            }
            return (False, feedback)
        
        # ✅ PASO 1: Validar el código del estudiante contra la solución con IA
        system_p = """Eres un experto evaluador de código C. Tu trabajo es determinar si el código del estudiante resuelve CORRECTAMENTE el problema.

CRITERIOS DE EVALUACIÓN:
1. El código DEBE resolver el problema descrito en la instrucción, de manera completa y correcta.
2. DEBE usar las estructuras y lógica apropiadas para C
3. DEBE funcionar correctamente (sin errores de sintaxis o lógica) 
4. NO puede ser código trivial o placeholder (como solo "return 0;" o comentarios)
5. DEBE mostrar esfuerzo genuino de resolver el problema
6. No puede ser un bosquejo, de estructura o código incompleto.

IMPORTANTE: Si el código es razonable y parece resolver el problema (aunque no sea perfecto), responde SI.
Responde NO si el código claramente NO resuelve el problema o tiene errores graves, o esta incompleto.

Sé JUSTO y dale crédito al estudiante si ha hecho un esfuerzo real."""
        
        user_p = f"""Instrucción del ejercicio:
{description}

Solución de referencia del profesor:
{solution}

Código del estudiante:
{user_response}

¿El código del estudiante resuelve CORRECTAMENTE el problema? Responde SOLO con SI o NO."""
        
        code_validation = await ask_llama_validator(system_p, user_p)
        code_is_correct = "SI" in code_validation.upper()
        
        # AI validation completed
        
        # ✅ PASO 2: Tests - POR AHORA marcar como None hasta implementar sandbox
        # TODO: Implementar ejecución real del código en sandbox
        test_is_correct = None  # None significa "no evaluado aún" o "no hay tests"
        
        # Si hay tests, por ahora asumimos que están correctos si el código es correcto
        # Esto es temporal hasta implementar el sandbox real
        if has_tests:
            # Tests detected but sandbox not implemented yet
            # For now, assuming correctness matches code validation
            test_is_correct = code_is_correct
        
        # Test validation completed
        
        # ✅ Construir feedback detallado
        feedback = {
            "code_is_correct": code_is_correct,
            "test_is_correct": test_is_correct,  # None si no hay tests, bool si hay
            "has_tests": has_tests
        }
        
        # ✅ Resultado final: POR AHORA solo basado en el código
        # Cuando implementemos sandbox, cambiar a: code_is_correct and (test_is_correct if has_tests else True)
        final_correct = code_is_correct
        
        # Validation result prepared
        
        return (final_correct, feedback)

    # 4. UNIT CONCEPTS (Relación de columnas)
    elif exercise_type == "unit_concepts":
        # El frontend envía: { "pairs": [{"concept": "X", "definition": "Y"}, ...] }
        # Debemos comparar con el dict 'concepts' del ejercicio: {"concepto": "definición"}
        correct_concepts = exercise.get("concepts", {})
        
        # Extraer el array de pares
        pairs = user_response.get("pairs", []) if isinstance(user_response, dict) else []
        
        if not pairs or len(pairs) != len(correct_concepts):
            return (False, None)
        
        # Convertir pares a dict para comparar
        user_dict = {pair.get("concept"): pair.get("definition") for pair in pairs}
        
        # Verificar que todos los pares sean correctos
        for concept, definition in correct_concepts.items():
            if user_dict.get(concept) != definition:
                return (False, None)
        
        return (True, None)

    # 5. STUDY (Progreso automático)
    elif exercise_type == "study":
        return (True, None)
        
    return (False, None)

async def update_user_streak(db: AsyncIOMotorDatabase, user_id: str, session_start_time: datetime) -> int:
    """
    Actualiza la racha de días consecutivos del usuario de forma atómica.
    """
    user_oid = ObjectId(user_id)
    user_doc = await db[USERS_COLLECTION].find_one({"_id": user_oid})
    
    if not user_doc:
        return 0

    # Obtenemos datos actuales (con valores por defecto si no existen)
    streak_data = user_doc.get("streak", {})
    current_streak = streak_data.get("current_days", 0)
    last_practice_date = streak_data.get("last_practice_date")

    # 1. Normalizar fechas a "Solo Día" (Midnight) para comparar calendarios
    # Usamos .date() para ignorar horas, minutos y segundos
    today_date = session_start_time.date()
    
    if last_practice_date:
        # Si last_practice_date es un datetime, extraemos solo la fecha
        last_date = last_practice_date.date() if isinstance(last_practice_date, datetime) else last_practice_date
        
        diff = (today_date - last_date).days

        if diff == 0:
            # YA PRACTICÓ HOY: No sumamos nada, mantenemos la racha
            new_streak = current_streak
        elif diff == 1:
            # DÍA CONSECUTIVO (Ayer): Incrementamos racha
            new_streak = current_streak + 1
        else:
            # SE ROMPIÓ LA RACHA (Pasó más de un día): Reiniciamos a 1
            new_streak = 1
    else:
        # PRIMERA VEZ QUE PRACTICA: Iniciamos en 1
        new_streak = 1

    # 2. Actualizar el documento del usuario
    # Guardamos la fecha completa para tener el registro exacto, 
    # pero la racha se basa en los días.
    await db[USERS_COLLECTION].update_one(
        {"_id": user_oid},
        {
            "$set": {
                "streak.current_days": new_streak,
                "streak.last_practice_date": session_start_time
            }
        }
    )
    
    return new_streak

# varificacion de leccion completa 
async def is_lesson_completed(db: AsyncIOMotorDatabase, user_id: str, lesson_id: str, module_id: str) -> bool:
    """
    DEPRECATED: Usar is_lesson_completed_v2 en su lugar.
    Comprueba si el usuario ha terminado todos los ejercicios de la lección.
    """
    # 1. Obtener el módulo para contar cuántos ejercicios tiene la lección
    module = await db[MODULES_COLLECTION].find_one({"_id": ObjectId(module_id)})
    if not module: return False
    
    # Buscar la lección específica dentro del array de lecciones
    lesson = next((l for l in module["lessons"] if str(l["_id"]) == lesson_id), None)
    if not lesson: return False
    
    total_exercises = len(lesson["exercises"])
    
    # 2. Contar cuántos ejercicios ÚNICOS ha completado el usuario en esta lección
    # Usamos $group para obtener UUIDs únicos con status="completed"
    pipeline = [
        {"$match": {
            "user_id": user_id,
            "lesson_id": lesson_id,
            "status": "completed"
        }},
        {"$group": {"_id": "$exercise_uuid"}},  # Agrupa por UUID único
        {"$count": "unique_completed"}  # Cuenta los grupos únicos
    ]
    
    result = await db[PROGRESS_COLLECTION].aggregate(pipeline).to_list(length=1)
    completed_count = result[0]["unique_completed"] if result else 0

    return completed_count >= total_exercises


async def is_lesson_completed_v2(db: AsyncIOMotorDatabase, user_id: str, lesson_id: str, module_id: str, session_id: str) -> bool:
    """
    NUEVA VERSIÓN: Verifica si se completaron todos los ejercicios en el intento actual.
    
    Lógica:
    1. Obtiene el número total de ejercicios de la lección
    2. Cuenta cuántos ejercicios se intentaron en la sesión actual
    3. Retorna True si se intentaron todos (independiente de si fueron correctos)
    """
    # 1. Obtener el módulo y contar ejercicios
    module = await db[MODULES_COLLECTION].find_one({"_id": ObjectId(module_id)})
    if not module:
        return False
    
    lesson = next((l for l in module["lessons"] if str(l["_id"]) == lesson_id), None)
    if not lesson:
        return False
    
    total_exercises = len(lesson["exercises"])
    
    # 2. Obtener el progreso de la lección (sin filtrar por session_id para detectar intentos previos)
    lesson_progress = await db["lesson_progress"].find_one({
        "user_id": user_id,
        "lesson_id": lesson_id
    })
    
    if not lesson_progress:
        return False
    
    # 3. Contar ejercicios únicos en la sesión ACTUAL
    # NOTA: El array "exercises" ya contiene solo los ejercicios de la sesión actual
    # porque se reinicia cuando hay un nuevo intento (sesión_id diferente)
    attempted_exercises = lesson_progress.get("exercises", [])
    unique_exercise_uuids = set(ex["exercise_uuid"] for ex in attempted_exercises)
    
    completed = len(unique_exercise_uuids) >= total_exercises
    
    # 4. Si se completó, marcar la lección como completada
    if completed and not lesson_progress.get("is_completed", False):
        await db["lesson_progress"].update_one(
            {"_id": lesson_progress["_id"]},
            {"$set": {"is_completed": True}}
        )
    
    return completed

async def can_retry_exercise(db: AsyncIOMotorDatabase, user_id: str, exercise_uuid: str, lesson_id: str) -> tuple[bool, str]:
    """
    Verifica si el usuario puede intentar un ejercicio.
    
    Reglas:
    1. Si ya lo completó (status="completed"), NO puede reintentarlo
    2. Si falló (status="failed"), solo puede reintentarlo cuando entre a otra lección y regrese
    
    Returns:
        (can_attempt: bool, reason: str)
    """
    # Buscar el último intento del usuario en este ejercicio
    last_attempt = await db[PROGRESS_COLLECTION].find_one(
        {
            "user_id": user_id,
            "exercise_uuid": exercise_uuid
        },
        sort=[("attempt_time", -1)]  # Más reciente primero
    )
    
    if not last_attempt:
        # Primer intento, puede intentarlo
        return (True, "")
    
    if last_attempt["status"] == "completed":
        # Ya lo completó, no puede reintentarlo
        return (False, "Ya completaste este ejercicio correctamente.")
    
    # Si falló, verificar si ha visitado otra lección desde entonces
    # Para eso, buscamos si hay algún intento posterior en OTRA lección
    has_other_attempts = await db[PROGRESS_COLLECTION].find_one({
        "user_id": user_id,
        "lesson_id": {"$ne": lesson_id},  # Diferente lección
        "attempt_time": {"$gt": last_attempt["attempt_time"]}  # Después del fallo
    })
    
    if has_other_attempts:
        # Ha visitado otra lección, puede reintentar
        return (True, "")
    else:
        # No ha visitado otra lección, no puede reintentar aún
        return (False, "Debes completar ejercicios de otra lección antes de reintentar este.")


# =================================================================
# SERVICIO PRINCIPAL
# =================================================================

async def register_progress_service(db: AsyncIOMotorDatabase, user_id: str, submission: ExerciseSubmission) -> ProgressResponse:
    """
    Progreso por LECCIÓN (no por ejercicio individual).
    
    Flujo:
    1. Buscar el registro de progreso de esta lección
    2. Si no existe, crearlo (primer intento)
    3. Si existe:
       - Si is_locked=True (examen), rechazar
       - Si no, permitir y actualizar solo si mejora el puntaje
    4. Agregar el ejercicio al array de intentos
    5. Validar y retornar resultado
    """
    # Progress tracking initiated
    
    # 1. Obtener la solución del ejercicio
    solution = await get_exercise_solution(
        db, submission.module_id, submission.lesson_id, submission.exercise_uuid
    )
    
    # 2. Validar la respuesta - ✅ Desempaquetar tupla (is_correct, feedback)
    is_correct, code_feedback = await check_solution(solution, submission.user_response)
    points_earned = solution.get("points", 0) if is_correct else 0
    
    print(f"✅ Ejercicio validado - is_correct: {is_correct}, points: {points_earned}")
    
    # 3. Buscar o crear el registro de progreso de LA LECCIÓN
    lesson_progress = await db["lesson_progress"].find_one({
        "user_id": user_id,
        "lesson_id": submission.lesson_id
    })
    
    # 3.5. NUEVO: Verificar si ya se envió este ejercicio en la sesión actual
    if lesson_progress:
        current_session = lesson_progress.get("session_id")
        if current_session == submission.session_id:
            # Verificar si este ejercicio ya está en el array
            exercises = lesson_progress.get("exercises", [])
            exercise_uuids = [ex.get("exercise_uuid") for ex in exercises]
            
            if submission.exercise_uuid in exercise_uuids:
                # Duplicate submission detected and rejected
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Este ejercicio ya fue enviado en la sesión actual. No se permiten envíos duplicados."
                )
    
    # 4. Verificar si es un examen bloqueado
    if lesson_progress and lesson_progress.get("is_locked", False):
        # Locked lesson: only one attempt allowed
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta lección es un examen y solo permite un intento."
        )
    
    # 5. Crear el objeto del ejercicio actual
    exercise_attempt = ExerciseAttempt(
        exercise_uuid=submission.exercise_uuid,
        user_response=submission.user_response,
        is_correct=is_correct,
        points_earned=points_earned
    )
    
    # 6. Actualizar o crear el progreso de la lección
    if lesson_progress is None:
        # PRIMER INTENTO de esta lección
        # First attempt: creating progress record
        
        lesson_progress_obj = LessonProgress(
            user_id=user_id,
            module_id=submission.module_id,
            lesson_id=submission.lesson_id,
            session_id=submission.session_id,
            exercises=[exercise_attempt],
            current_score=points_earned,
            best_score=points_earned,
            attempt_count=1
        )
        
        await db["lesson_progress"].insert_one(
            lesson_progress_obj.model_dump(by_alias=True, exclude={"id"})
        )
        
        # Actualizar XP del usuario
        await db[USERS_COLLECTION].update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"total_points": points_earned}}
        )
        
    else:
        # REINTENTO de la lección
        # Retry attempt detected
        
        # Verificar si es un nuevo intento (diferente session_id)
        is_new_attempt = lesson_progress.get("session_id") != submission.session_id
        
        if is_new_attempt:
            # New session: incrementing attempt
            # Nuevo intento: reiniciar ejercicios y puntaje
            await db["lesson_progress"].update_one(
                {"_id": lesson_progress["_id"]},
                {
                    "$set": {
                        "session_id": submission.session_id,
                        "exercises": [exercise_attempt.model_dump()],
                        "current_score": points_earned,
                        "last_attempt": datetime.utcnow()
                    },
                    "$inc": {"attempt_count": 1}
                }
            )
        else:
            # Misma sesión: agregar ejercicio al array
            # Adding to current attempt
            await db["lesson_progress"].update_one(
                {"_id": lesson_progress["_id"]},
                {
                    "$push": {"exercises": exercise_attempt.model_dump()},
                    "$inc": {"current_score": points_earned},
                    "$set": {"last_attempt": datetime.utcnow()}
                }
            )
        
        # Obtener el progreso actualizado
        lesson_progress = await db["lesson_progress"].find_one({"_id": lesson_progress["_id"]})
        current_score = lesson_progress["current_score"]
        best_score = lesson_progress["best_score"]
        
        # Si el puntaje actual supera el mejor, actualizar XP
        if current_score > best_score:
            xp_diff = current_score - best_score
            # New high score achieved
            
            await db["lesson_progress"].update_one(
                {"_id": lesson_progress["_id"]},
                {"$set": {"best_score": current_score}}
            )
            
            await db[USERS_COLLECTION].update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {"total_points": xp_diff}}
            )
        else:
            # Score is not improved
            pass
    
    # 7. Verificar si la lección está completa
    lesson_finished = await is_lesson_completed_v2(
        db, user_id, submission.lesson_id, submission.module_id, submission.session_id
    )
    
    # Lesson completion status checked
    
    # 7.5. 🆕 Si es una lección privada y se completó, bloquearlo para siempre
    if lesson_finished:
        # Obtener la lección para verificar si es privada
        module = await db[MODULES_COLLECTION].find_one({"_id": ObjectId(submission.module_id)})
        if module:
            lesson = next((l for l in module["lessons"] if str(l["_id"]) == submission.lesson_id), None)
            if lesson and lesson.get("is_private", False):
                # Bloquear el progreso de esta lección permanentemente
                await db["lesson_progress"].update_one(
                    {"user_id": user_id, "lesson_id": submission.lesson_id},
                    {"$set": {"is_locked": True}}
                )
                # Locked lesson: private lessons cannot be retaken
    
    # 8. Obtener current_score y total_possible para el frontend
    # Obtener el progreso actualizado
    lesson_progress_updated = await db["lesson_progress"].find_one({
        "user_id": user_id,
        "lesson_id": submission.lesson_id
    })
    
    current_score = lesson_progress_updated.get("current_score", 0) if lesson_progress_updated else 0
    total_possible = lesson_progress_updated.get("total_possible", 0) if lesson_progress_updated else 0
    
    # Si total_possible no está calculado, calcularlo ahora
    if total_possible == 0:
        module = await db[MODULES_COLLECTION].find_one({"_id": ObjectId(submission.module_id)})
        if module:
            lesson = next((l for l in module["lessons"] if str(l["_id"]) == submission.lesson_id), None)
            if lesson:
                total_possible = sum(e.get("points", 0) for e in lesson.get("exercises", []))
                # Actualizar en la BD para futuros usos
                await db["lesson_progress"].update_one(
                    {"_id": lesson_progress_updated["_id"]},
                    {"$set": {"total_possible": total_possible}}
                )
    
    print(f"📊 Puntaje actual: {current_score}/{total_possible}")
    
    # 9. Retornar respuesta
    return ProgressResponse(
        is_correct=is_correct,
        lesson_finished=lesson_finished,
        points_earned=points_earned,
        current_score=current_score,
        total_possible=total_possible,
        code_feedback=code_feedback  # ✅ Incluir feedback para make_code
    )


async def get_user_global_progress_service(db: AsyncIOMotorDatabase, user_id: str) -> List[dict]:
    """Devuelve la lista completa de registros de progreso para un usuario.

    Normaliza el campo `_id` a string para facilitar la serialización JSON.
    """
    # Buscamos por user_id tal cual (en este proyecto se almacena como string)
    cursor = db[PROGRESS_COLLECTION].find({"user_id": user_id}).sort("attempt_time", -1)
    docs = await cursor.to_list(length=1000)

    # Normalizar ObjectId a str en `_id` si existe
    for d in docs:
        if "_id" in d:
            d["_id"] = str(d["_id"])
    return docs

async def get_user_progress_summary(db: AsyncIOMotorDatabase, user_id: str) -> UserProgressSummary:
    """
    Obtiene un resumen del progreso del usuario (puntos, racha y ejercicios completados).
    """
    user_oid = ObjectId(user_id)
    
    # 1. Obtener el documento del usuario (para puntos y racha)
    user_doc = await db[USERS_COLLECTION].find_one({"_id": user_oid})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    # 2. Obtener todos los UUIDs de ejercicios que el usuario ha completado (status="completed")
    # Usamos $project y $group para obtener una lista única de UUIDs completados.
    
    completed_uuid_docs = await db[PROGRESS_COLLECTION].aggregate([
        {"$match": {"user_id": user_id, "status": "completed"}},
        {"$group": {"_id": "$exercise_uuid"}} # Agrupamos por UUID para obtener una lista única
    ]).to_list(None)

    # 3. Extraer la lista de UUIDs
    completed_uuids = [doc["_id"] for doc in completed_uuid_docs]

    # 4. Combinar datos del usuario y el progreso
    
    # Creamos un diccionario base con los datos del usuario
    summary_data = {
        "user_id": str(user_doc["_id"]),
        "username": user_doc["username"],
        "total_points": user_doc.get("total_points", 0),
        "streak": user_doc.get("streak", {"current_days": 0}), # Aseguramos que 'streak' exista
        "completed_exercises": completed_uuids,
    }

    # Usamos UserProgressSummary para la validación y serialización
    return UserProgressSummary.model_validate(summary_data)