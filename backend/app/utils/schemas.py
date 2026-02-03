"""
📋 ESQUEMAS DE ENTRADA PARA MÓDULOS, LECCIONES Y EJERCICIOS
===========================================================

Este archivo documenta exactamente qué estructura espera el backend
para crear módulos, lecciones y ejercicios vía API.

Usar como referencia cuando prepares los datos en Excel/CSV/JSON
para asegurar que coincidan exactamente con lo que espera la API.
"""

# ============================================================================
# 1. ESTRUCTURA DE EJERCICIOS (EXERCISES)
# ============================================================================

"""
Los ejercicios deben enviarse dentro de las lecciones con esta estructura:

Cada ejercicio DEBE tener:
  - type: string (uno de: "question", "complete", "make_code", "study", "unit_concepts")
  - title: string (título del ejercicio)
  - points: integer (puntos que otorga)

Campos adicionales SEGÚN el tipo:
"""

# ---- TIPO: "question" (Opción Múltiple) ----
QUESTION_EXERCISE = {
    "type": "question",
    "title": "¿Cuál es la declaración correcta de una variable?",
    "points": 5,
    "description": "Selecciona la respuesta correcta",
    "options": [
        "int x = 5;",
        "x int = 5;",
        "variable x = 5;",
        "5 = x int;"
    ],
    "correct_answer": "int x = 5;"
}

# ---- TIPO: "complete" (Completar Código) ----
COMPLETE_EXERCISE = {
    "type": "complete",
    "title": "Completa la línea",
    "points": 10,
    "text": "Para declarar un entero usamos: ___",
    "options": [
        "int x;",
        "float x;",
        "char x;",
        "string x;"
    ],
    "correct_answer": "int x;"
}

# ---- TIPO: "make_code" (Escribir Código) ----
MAKE_CODE_EXERCISE = {
    "type": "make_code",
    "title": "Escribe un programa Hola Mundo",
    "points": 15,
    "description": "Escribe un programa en C que imprima 'Hola Mundo'",
    "code": "",
    "solution": "#include <stdio.h>\nint main() {\n    printf(\"Hola Mundo\\n\");\n    return 0;\n}",
    "test_cases": [
        {
            "input": "",
            "expected_output": "Hola Mundo"
        }
    ]
}

# ---- TIPO: "study" (Tarjetas de Estudio) ----
STUDY_EXERCISE = {
    "type": "study",
    "title": "Palabras clave de C",
    "points": 5,
    "flashcards": {
        "printf": "Función para imprimir texto en pantalla",
        "scanf": "Función para leer entrada del usuario",
        "int": "Tipo de dato para números enteros",
        "#include": "Directiva para incluir librerías"
    }
}

# ---- TIPO: "unit_concepts" (Conceptos Unitarios) ----
UNIT_CONCEPTS_EXERCISE = {
    "type": "unit_concepts",
    "title": "Conceptos de Variables",
    "points": 5,
    "concepts": {
        "variable": "Un contenedor con nombre que almacena un valor",
        "tipo_dato": "Especifica qué tipo de valor puede almacenar",
        "declaración": "Proceso de crear una variable",
        "inicialización": "Asignar un valor inicial a una variable"
    }
}

# Tabla de campos requeridos por tipo
EXERCISE_FIELDS_BY_TYPE = {
    "question": ["type", "title", "points", "description", "options", "correct_answer"],
    "complete": ["type", "title", "points", "text", "options", "correct_answer"],
    "make_code": ["type", "title", "points", "description", "code", "solution", "test_cases"],
    "study": ["type", "title", "points", "flashcards"],
    "unit_concepts": ["type", "title", "points", "concepts"],
}


# ============================================================================
# 2. ESTRUCTURA DE LECCIONES (LESSONS)
# ============================================================================

"""
Cada lección DEBE tener:
  - title: string
  - description: string
  - order: integer (número de orden dentro del módulo: 1, 2, 3...)
  - xp_reward: integer (XP que se otorga al completar la lección)
  - is_private: boolean (true = examen/un intento, false = práctica/múltiples intentos)
  - exercises: array de ejercicios (MÍNIMO 1 ejercicio)
"""

LESSON_STRUCTURE = {
    "title": "Nombre de la Lección",
    "description": "Descripción de la lección",
    "order": 1,
    "xp_reward": 100,
    "is_private": False,
    "exercises": [
        # Array de ejercicios (ver ejemplos arriba)
        QUESTION_EXERCISE,
        STUDY_EXERCISE
    ]
}

LESSON_FIELDS_REQUIRED = ["title", "description", "order", "xp_reward", "is_private", "exercises"]


# ============================================================================
# 3. ESTRUCTURA DE MÓDULOS (MODULES)
# ============================================================================

"""
Cada módulo DEBE tener:
  - title: string
  - description: string
  - order: integer (número de orden en el curso: 1, 2, 3...)
  - estimate_time: integer (tiempo estimado en minutos)
  - lessons: array de lecciones (MÍNIMO 1 lección)
"""

MODULE_STRUCTURE = {
    "title": "Introducción a C",
    "description": "Aprende los conceptos básicos del lenguaje de programación C",
    "order": 1,
    "estimate_time": 180,
    "lessons": [
        # Array de lecciones (ver LESSON_STRUCTURE)
        {
            "title": "¿Qué es C?",
            "description": "Introducción al lenguaje C y su historia",
            "order": 1,
            "xp_reward": 50,
            "is_private": False,
            "exercises": [
                QUESTION_EXERCISE,
                STUDY_EXERCISE
            ]
        },
        {
            "title": "Variables y Tipos de Datos",
            "description": "Aprende a declarar variables y usar los tipos fundamentales",
            "order": 2,
            "xp_reward": 100,
            "is_private": False,
            "exercises": [
                COMPLETE_EXERCISE,
                UNIT_CONCEPTS_EXERCISE
            ]
        }
    ]
}

MODULE_FIELDS_REQUIRED = ["title", "description", "order", "estimate_time", "lessons"]


# ============================================================================
# 4. VALIDACIONES Y RESTRICCIONES
# ============================================================================

"""
VALIDACIONES IMPORTANTES:

1. EJERCICIOS:
   - Cada tipo debe tener exactamente sus campos requeridos
   - No pueden faltar campos obligatorios
   - Si el JSON tiene un campo mal, el backend rechaza con 422 Unprocessable Entity

2. LECCIONES:
   - MÍNIMO 1 ejercicio por lección (min_items=1)
   - XP reward > 0
   - Order debe ser único dentro del módulo
   - is_private: true = un intento, false = múltiples intentos

3. MÓDULOS:
   - MÍNIMO 1 lección por módulo (min_items=1)
   - Order debe ser único en toda la base de datos
   - estimate_time en minutos (numérico)

4. TIPOS DE DATO:
   - Strings: texto entre comillas
   - Integer: número sin decimales
   - Boolean: true o false (sin comillas)
   - Array: [...] con elementos dentro
   - Object: {...} con pares clave-valor
"""

VALIDATION_RULES = {
    "min_exercises_per_lesson": 1,
    "min_lessons_per_module": 1,
    "xp_reward_min": 1,
    "order_must_be_unique": "Dentro del padre (módulo para lecciones, lección para ejercicios)",
    "estimate_time_unit": "minutos",
    "is_private": "true=examen/un intento, false=práctica/múltiples intentos"
}


# ============================================================================
# 5. EJEMPLO COMPLETO (JSON para copiar-pegar en ThunderClient)
# ============================================================================

COMPLETE_EXAMPLE = {
    "title": "Introducción a C - Módulo 1",
    "description": "Aprende los conceptos básicos del lenguaje de programación C",
    "order": 1,
    "estimate_time": 180,
    "lessons": [
        {
            "title": "¿Qué es C?",
            "description": "Introducción al lenguaje C y su historia",
            "order": 1,
            "xp_reward": 50,
            "is_private": False,
            "exercises": [
                {
                    "type": "question",
                    "title": "¿En qué año fue creado C?",
                    "points": 5,
                    "description": "Selecciona la respuesta correcta",
                    "options": ["1972", "1982", "1992", "2002"],
                    "correct_answer": "1972"
                },
                {
                    "type": "study",
                    "title": "Características de C",
                    "points": 10,
                    "flashcards": {
                        "Lenguaje de bajo nivel": "Acceso a memoria con punteros",
                        "Eficiente": "Código compilado y rápido",
                        "Portable": "Se puede compilar en diferentes sistemas"
                    }
                }
            ]
        },
        {
            "title": "Variables y Tipos de Datos",
            "description": "Aprende a declarar variables y usar los tipos de datos",
            "order": 2,
            "xp_reward": 100,
            "is_private": False,
            "exercises": [
                {
                    "type": "question",
                    "title": "¿Cuál es la forma correcta de declarar una variable?",
                    "points": 5,
                    "description": "Elige la declaración válida",
                    "options": [
                        "int numero = 10;",
                        "numero int = 10;",
                        "variable numero = 10;",
                        "10 = numero int;"
                    ],
                    "correct_answer": "int numero = 10;"
                }
            ]
        }
    ]
}


# ============================================================================
# 6. REFERENCIAS RÁPIDAS
# ============================================================================

"""
COPIAR Y PEGAR RÁPIDO:

Para QUESTION:
{
  "type": "question",
  "title": "Pregunta aquí",
  "points": 5,
  "description": "Descripción",
  "options": ["A", "B", "C", "D"],
  "correct_answer": "A"
}

Para COMPLETE:
{
  "type": "complete",
  "title": "Completar",
  "points": 10,
  "text": "Texto con ___",
  "options": ["opción1", "opción2"],
  "correct_answer": "opción1"
}

Para MAKE_CODE:
{
  "type": "make_code",
  "title": "Código",
  "points": 15,
  "description": "Descripción",
  "code": "",
  "solution": "código aquí",
  "test_cases": [{"input": "", "expected_output": "output"}]
}

Para STUDY:
{
  "type": "study",
  "title": "Estudio",
  "points": 5,
  "flashcards": {"término": "definición"}
}

Para UNIT_CONCEPTS:
{
  "type": "unit_concepts",
  "title": "Conceptos",
  "points": 5,
  "concepts": {"término": "definición"}
}
"""
