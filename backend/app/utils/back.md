# 🏗️ ARQUITECTURA Y ESTADO ACTUAL DEL BACKEND

> **Proyecto**: CodeUP - Plataforma Interactiva para el Aprendizaje de Programación en C  
> **Framework**: FastAPI 0.116.2  
> **Base de Datos**: MongoDB (Motor AsyncIO)  
> **Autenticación**: JWT con bcrypt  
> **Última actualización**: 25 de diciembre de 2025

---

## � ÍNDICE
1. [Información General](#información-general)
2. [Arquitectura de Datos](#arquitectura-de-datos)
3. [Estructura de Colecciones](#estructura-de-colecciones)
4. [API Endpoints](#api-endpoints)
5. [Modelos de Datos](#modelos-de-datos)
6. [Sistema de Autenticación](#sistema-de-autenticación)
7. [Estado Actual del Backend](#estado-actual-del-backend)
8. [Flujo de Trabajo](#flujo-de-trabajo)
9. [Consideraciones para Frontend](#consideraciones-para-frontend)

---

## 1. INFORMACIÓN GENERAL

### 🎯 Descripción del Proyecto
Aplicación de aprendizaje de programación en C tipo Duolingo, con módulos, lecciones y ejercicios interactivos. Sistema de gamificación con puntos, recompensas y streaks.

### 🛠️ Stack Tecnológico
- **Framework**: FastAPI 0.116.2
- **Base de Datos**: MongoDB (Motor AsyncIO)
- **Autenticación**: JWT (HS256) con bcrypt
- **Validación**: Pydantic v2
- **Servidor**: Uvicorn
- **Compilación C**: Judge0 API

### 📁 Estructura del Proyecto
```
backend/app/
├── main.py              # Punto de entrada de la aplicación
├── models.py            # Modelos de datos principales
├── requirements.txt     # Dependencias del proyecto
├── env.env             # Variables de entorno
├── db/
│   └── db.py           # Configuración de MongoDB
├── routers/            # Endpoints de la API
│   ├── users.py
│   ├── modules.py
│   ├── lessons.py
│   ├── exercises.py
│   ├── progress.py
│   ├── rewards.py
│   └── sessions.py
├── schemas/            # Esquemas de validación Pydantic
│   ├── users.py
│   ├── modules.py
│   ├── lessons.py
│   ├── exercises.py
│   ├── progress.py
│   ├── rewards.py
│   └── sessions.py
├── services/           # Lógica de negocio
│   ├── users.py
│   ├── modules.py
│   ├── lessons.py
│   ├── exercises.py
│   ├── progress.py
│   ├── rewards.py
│   ├── sessions.py
│   ├── compiler.py     # Integración con Judge0
│   └── ai_service.py   # Validación con IA
└── utils/              # Utilidades y helpers
    ├── user.py
    └── lesson.py
```

### 🌐 URLs del Proyecto
- **Desarrollo**: http://127.0.0.1:8000
- **Documentación**: http://127.0.0.1:8000/docs (Swagger UI)
- **ReDoc**: http://127.0.0.1:8000/redoc

### 🔗 Configuración de MongoDB
- **URI**: mongodb+srv://FdezCompas:Fdez2003@cluster1.389ur.mongodb.net/
- **Base de Datos**: "code"
- **Colecciones**: users, modules, lessons, exercises, rewards, sessions, user_progress

---

## 2. ARQUITECTURA DE DATOS

### 🎯 Diseño Principal: Documentos Embebidos

Tu proyecto usa **documentos embebidos (embedded documents)** en MongoDB:

```
Módulo (Document Root)
├── title
├── description
├── order
├── estimate_time
└── lessons: [ (Array Embebido)
    ├── Lección 1
    │   ├── _id
    │   ├── title
    │   ├── description
    │   ├── order
    │   ├── xp_reward
    │   └── exercises: [ (Array Embebido)
    │       ├── Ejercicio 1
    │       │   ├── exercise_uuid
    │       │   ├── type (study, complete, question, make_code, unit_concepts)
    │       │   ├── title
    │       │   ├── points
    │       │   └── [campos específicos del tipo]
    │       ├── Ejercicio 2
    │       └── ...
    │   ]
    ├── Lección 2
    └── ...
]
```

### ✅ VENTAJAS de esta arquitectura
1. **Todo en un solo lugar**: Un módulo contiene TODA su información
2. **Atomicidad**: Una operación afecta un solo documento
3. **Performance**: Una sola consulta trae todo el módulo completo
4. **Simplicidad**: No hay JOINs ni referencias complejas
5. **Escalabilidad**: Perfecto para contenido educativo estructurado

### 🚫 Lo que NO necesitas hacer
- ❌ Consultas separadas para cada lección
- ❌ Consultas separadas para cada ejercicio
- ❌ JOINs complejos entre colecciones
- ❌ Gestión de relaciones muchos-a-muchos

---

---

## 3. ESTRUCTURA DE COLECCIONES EN MONGODB

### 3.1. � users (Usuarios)
```json
{
  "_id": ObjectId,
  "username": String,                    // Nombre de usuario único
  "email": String,                       // Correo electrónico único
  "password_hash": String,               // Hash de la contraseña (bcrypt)
  "role": String,                        // "student" o "teacher"
  "created_at": Date,                    // Fecha de creación de la cuenta
  "streak": {
    "current_days": Number,              // Días consecutivos de práctica
    "last_practice_date": Date           // Fecha de última práctica
  },
  "total_points": Number,                // Puntos totales acumulados
  "last_session_id": ObjectId           // Referencia a la última sesión
}
```

### 3.2. 📚 modules (Módulos) - **COLECCIÓN PRINCIPAL**
```json
{
  "_id": ObjectId,
  "title": String,                       // Título del módulo
  "description": String,                 // Descripción detallada del contenido
  "order": Number,                       // Orden del módulo en el curso
  "estimate_time": Number,               // Tiempo estimado en minutos
  "lessons": [                           // Array de lecciones embebidas
    {
      "_id": ObjectId,                   // ID de la lección
      "title": String,                   // Título de la lección
      "description": String,             // Descripción de la lección
      "order": Number,                   // Orden dentro del módulo
      "xp_reward": Number,               // Recompensa en puntos XP
      "exercises": [                     // Array de ejercicios embebidos
        {
          "exercise_uuid": String,       // UUID único del ejercicio
          "type": String,                // "study", "complete", "make_code", "question", "unit_concepts"
          "title": String,               // Título del ejercicio
          "points": Number,              // Puntos que otorga
          "order": Number,               // Orden dentro de la lección
          
          // ⬇️ Campos específicos según el tipo ⬇️
          
          // Para type: "study"
          "flashcards": {                // Diccionario palabra-definición
            "concepto": "definición"
          },
          
          // Para type: "complete"
          "text": String,                // Texto con espacios en blanco
          "options": [String],           // Opciones disponibles
          "correct_answer": String,      // Respuesta correcta
          
          // Para type: "make_code"
          "description": String,         // Descripción del problema
          "code": String,                // Código inicial/plantilla
          "solution": String,            // Solución correcta (opcional)
          "test_cases": [                // Casos de prueba
            {
              "input": String,           // Entrada del caso
              "expected_output": String  // Salida esperada
            }
          ],
          
          // Para type: "question"
          "description": String,         // La pregunta
          "options": [String],           // Opciones de respuesta
          "correct_answer": String,      // Respuesta correcta
          
          // Para type: "unit_concepts"
          "description": String,         // Descripción general
          "concepts": {                  // Diccionario concepto-definición
            "concepto": "definición"
          }
        }
      ]
    }
  ]
}
```

### 3.3. 📊 user_progress (Progreso del Usuario)
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,                  // Referencia al usuario
  "module_id": ObjectId,                // Referencia al módulo
  "lesson_id": ObjectId,                // Referencia a la lección
  "exercise_uuid": String,              // UUID del ejercicio
  "status": String,                     // "not_started", "in_progress", "completed"
  "attempts": [                         // Historial de intentos
    {
      "code": String,                   // Código escrito por el usuario
      "is_correct": Boolean,            // Si el intento fue correcto
      "points_earned": Number,          // Puntos ganados en este intento
      "submitted_at": Date              // Timestamp del intento
    }
  ],
  "last_session_id": ObjectId,          // Última sesión de trabajo
  "is_mastered": Boolean,               // Si el ejercicio ha sido dominado
  "total_points_earned": Number,        // Total de puntos ganados
  "completed_at": Date                  // Fecha de completitud (si aplica)
}
```

### 3.4. 📅 sessions (Sesiones de Estudio)
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,                  // Referencia al usuario
  "lesson_id": ObjectId,                // Referencia a la lección
  "start_time": Date,                   // Momento de inicio de la sesión
  "end_time": Date,                     // Momento de fin (null si está activa)
  "duration_minutes": Number,            // Duración en minutos
  "status": String,                     // "in_progress", "completed"
  "exercises_completed": Number,         // Ejercicios completados en esta sesión
  "total_points_gained": Number         // Puntos ganados en esta sesión
}
```

### 3.5. 🏆 rewards (Recompensas)
```json
{
  "_id": ObjectId,
  "name": String,                       // Nombre de la recompensa
  "description": String,                 // Descripción de la recompensa
  "type": String,                       // "streak", "perfect_lesson", "milestone", etc.
  "points": Number,                     // Puntos que otorga la recompensa
  "icon": String,                       // URL o nombre del icono
  "condition": Object,                  // Condiciones para obtenerla
  "users_awarded": [ObjectId],          // Array de usuarios que ya la obtuvieron
  "created_at": Date                    // Fecha de creación
}
```

### 📝 NOTAS IMPORTANTES
- Los ejercicios están **embebidos en modules**, no en colección separada
- Los ObjectId se convierten a String en las respuestas JSON de la API
- Los UUID de ejercicios permiten identificación única dentro de lecciones
- El progreso del usuario se rastrea por ejercicio individual usando UUID
- Las sesiones pueden estar activas (end_time = null) o completadas

---

---

## 4. API ENDPOINTS

> **⚠️ IMPORTANTE**: El acceso principal al contenido es a través de `/modules/`.  
> Los módulos contienen lecciones y ejercicios embebidos, por lo que una sola llamada trae todo.

### 4.1. 👤 USUARIOS (/users)

#### `POST /users/register`
- **Descripción**: Registro de nuevo estudiante
- **Autenticación**: No requerida
- **Body**: 
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```
- **Response**: UserResponse (201)

#### `POST /users/register_teacher`
- **Descripción**: Registro de profesor (requiere clave secreta)
- **Autenticación**: No requerida
- **Body**: Igual que register + secret_key
- **Response**: UserResponse (201)

#### `POST /users/login`
- **Descripción**: Inicio de sesión (retorna JWT token)
- **Autenticación**: No requerida
- **Body**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Response**: Token (200)
  ```json
  {
    "access_token": "string",
    "token_type": "bearer"
  }
  ```

#### `GET /users/me`
- **Descripción**: Obtener usuario actual autenticado
- **Autenticación**: ✅ Requerida
- **Response**: UserResponse (200)

#### `GET /users/`
- **Descripción**: Listar usuarios (con filtro opcional por rol)
- **Autenticación**: ✅ Requerida
- **Query Params**: `?role=student` o `?role=teacher`
- **Response**: List[UserResponse] (200)

#### `GET /users/{user_id}`
- **Descripción**: Ver usuario específico
- **Autenticación**: ✅ Requerida
- **Response**: UserResponse (200)

---

### 4.2. 📚 MÓDULOS (/modules) - **PUNTO DE ENTRADA PRINCIPAL**

> **📌 FLUJO PRINCIPAL**: Los módulos son el punto de acceso principal.  
> Contienen lecciones y ejercicios embebidos.

#### `GET /modules/`
- **Descripción**: Obtener **TODOS** los módulos con lecciones y ejercicios incluidos
- **Autenticación**: No requerida
- **Response**: List[ModuleOut] (200)
- **Nota**: Este es el endpoint principal para obtener todo el contenido

#### `GET /modules/{module_id}`
- **Descripción**: Obtener módulo específico con **TODAS** sus lecciones y ejercicios
- **Autenticación**: No requerida
- **Response**: ModuleOut (200)

#### `POST /modules/`
- **Descripción**: Crear nuevo módulo (con lecciones y ejercicios embebidos)
- **Autenticación**: ✅ Requerida (Teacher)
- **Body**: ModuleCreate
  ```json
  {
    "title": "string",
    "description": "string",
    "order": 1,
    "estimate_time": 120,
    "lessons": [
      {
        "title": "string",
        "description": "string",
        "order": 1,
        "xp_reward": 100,
        "exercises": [...]
      }
    ]
  }
  ```
- **Response**: ModuleOut (201)

#### `PUT /modules/{module_id}`
- **Descripción**: Actualizar módulo (incluyendo lecciones y ejercicios)
- **Autenticación**: ✅ Requerida (Teacher)
- **Body**: ModuleUpdate
- **Response**: ModuleOut (200)
- **Capacidades**:
  - ✅ Editar título, descripción del módulo
  - ✅ Agregar lecciones nuevas (sin `_id`)
  - ✅ Editar lecciones existentes (con `_id`)
  - ✅ Agregar ejercicios a lecciones
  - ✅ Editar ejercicios existentes
  - ✅ Eliminar lecciones (omitir del array)
  - ✅ Eliminar ejercicios (omitir del array)

#### `DELETE /modules/{module_id}`
- **Descripción**: Eliminar módulo completo
- **Autenticación**: ✅ Requerida (Teacher)
- **Response**: 204 No Content

---

### 4.3. 📖 LECCIONES (/lessons) - **ENDPOINTS DE RESPALDO**

> **⚠️ NOTA**: Estos endpoints son para casos específicos.  
> El acceso normal es a través de `/modules/`

#### `GET /lessons/{lesson_id}`
- **Descripción**: Obtener lección por ID (uso de respaldo)
- **Autenticación**: No requerida
- **Response**: LessonOut (200)

#### `POST /lessons/`
- **Descripción**: Crear lección independiente (uso de respaldo)
- **Autenticación**: ✅ Requerida (Teacher)
- **Body**: LessonCreate
- **Response**: LessonOut (201)
- **Nota**: Normalmente las lecciones se crean dentro de módulos

#### `PUT /lessons/{lesson_id}`
- **Descripción**: Actualizar lección (uso de respaldo)
- **Autenticación**: ✅ Requerida (Teacher)
- **Response**: LessonOut (200)

#### `DELETE /lessons/{lesson_id}`
- **Descripción**: Eliminar lección (uso de respaldo)
- **Autenticación**: ✅ Requerida (Teacher)
- **Response**: 204 No Content

---

### 4.4. 📝 EJERCICIOS (/exercises) - **ENDPOINTS ESPECÍFICOS**

#### `GET /exercises/{exercise_id}`
- **Descripción**: Obtener ejercicio por ID (para casos específicos)
- **Autenticación**: No requerida
- **Response**: ExerciseOut (200)
- **Uso**: Normalmente se accede a través de `/modules/{module_id}`

#### `GET /exercises/strict/{exercise_id}`
- **Descripción**: Obtener ejercicio con validación estricta
- **Autenticación**: No requerida
- **Response**: ExerciseSchema (200)
- **Uso**: Útil para formularios de edición

#### `POST /exercises/create`
- **Descripción**: Crear ejercicio independiente (caso específico)
- **Autenticación**: No requerida
- **Body**: ExerciseCreate
- **Response**: ExerciseOut (201)
- **Nota**: Normalmente se crean dentro de lecciones

---

### 4.5. 📊 PROGRESO (/progress)

#### `POST /progress/exercise`
- **Descripción**: Registrar intento de ejercicio
- **Autenticación**: ✅ Requerida
- **Body**:
  ```json
  {
    "user_id": "string",
    "exercise_uuid": "string",
    "lesson_id": "string",
    "module_id": "string",
    "code": "string",
    "session_id": "string"
  }
  ```
- **Response**: ProgressResponse (200)
- **Funcionalidad**:
  - ✅ Valida el código del usuario
  - ✅ Calcula puntos proporcionales
  - ✅ Actualiza progreso del usuario
  - ✅ Actualiza puntos totales

#### `GET /progress/user/{user_id}`
- **Descripción**: Ver progreso completo de un usuario
- **Autenticación**: ✅ Requerida
- **Response**: List[ProgressOut] (200)
- **Incluye**: Todos los ejercicios intentados, estado, puntos

---

### 4.6. 📅 SESIONES (/sessions)

#### `POST /sessions/start`
- **Descripción**: Iniciar sesión de estudio
- **Autenticación**: ✅ Requerida
- **Body**:
  ```json
  {
    "user_id": "string",
    "lesson_id": "string"
  }
  ```
- **Response**: SessionOut (201)

#### `PUT /sessions/{session_id}/end`
- **Descripción**: Finalizar sesión de estudio
- **Autenticación**: ✅ Requerida
- **Response**: SessionOut (200)
- **Funcionalidad**:
  - ✅ Calcula duración
  - ✅ Actualiza streak del usuario
  - ✅ Registra ejercicios completados

#### `GET /sessions/user/{user_id}`
- **Descripción**: Ver historial de sesiones de un usuario
- **Autenticación**: ✅ Requerida
- **Response**: List[SessionOut] (200)

---

### 4.7. 🏆 RECOMPENSAS (/rewards)

#### `GET /rewards/`
- **Descripción**: Listar todas las recompensas
- **Autenticación**: No requerida
- **Response**: List[RewardOut] (200)

#### `GET /rewards/user/{user_id}`
- **Descripción**: Recompensas de un usuario específico
- **Autenticación**: ✅ Requerida
- **Response**: List[RewardOut] (200)

#### `GET /rewards/available`
- **Descripción**: Recompensas disponibles (no obtenidas)
- **Autenticación**: ✅ Requerida
- **Query Param**: `?user_id=string`
- **Response**: List[RewardOut] (200)

#### `GET /rewards/stats`
- **Descripción**: Estadísticas de recompensas
- **Autenticación**: ✅ Requerida
- **Response**: RewardStatsOut (200)

#### `POST /rewards/`
- **Descripción**: Crear nueva recompensa
- **Autenticación**: ✅ Requerida (Teacher)
- **Body**: RewardCreate
- **Response**: RewardOut (201)

#### `PUT /rewards/{reward_id}`
- **Descripción**: Editar recompensa existente
- **Autenticación**: ✅ Requerida (Teacher)
- **Body**: RewardUpdate
- **Response**: RewardOut (200)

#### `DELETE /rewards/{reward_id}`
- **Descripción**: Eliminar recompensa
- **Autenticación**: ✅ Requerida (Teacher)
- **Response**: 204 No Content

---

---

## 5. MODELOS DE DATOS Y TIPOS DE EJERCICIOS

### 5.1. Tipos de Ejercicios

#### 📖 STUDY (Estudio con Flashcards)
```json
{
  "type": "study",
  "title": "Conceptos básicos",
  "points": 10,
  "flashcards": {
    "variable": "Espacio en memoria para almacenar datos",
    "función": "Bloque de código reutilizable",
    "array": "Colección de elementos del mismo tipo"
  }
}
```

#### ✏️ COMPLETE (Completar espacios)
```json
{
  "type": "complete",
  "title": "Completa el código",
  "points": 20,
  "text": "El lenguaje C es un lenguaje de programación ___",
  "options": ["compilado", "interpretado", "híbrido"],
  "correct_answer": "compilado"
}
```

#### 💻 MAKE_CODE (Programación)
```json
{
  "type": "make_code",
  "title": "Programa Hola Mundo",
  "points": 50,
  "description": "Escribe un programa que imprima 'Hola Mundo'",
  "code": "#include <stdio.h>\nint main() {\n    // Tu código aquí\n    return 0;\n}",
  "solution": "#include <stdio.h>\nint main() {\n    printf(\"Hola Mundo\");\n    return 0;\n}",
  "test_cases": [
    {
      "input": "",
      "expected_output": "Hola Mundo"
    }
  ]
}
```
**Validación**: Se usa Judge0 API para compilar y ejecutar

#### ❓ QUESTION (Pregunta de opción múltiple)
```json
{
  "type": "question",
  "title": "Función principal",
  "points": 15,
  "description": "¿Cuál es la función principal en C?",
  "options": ["main()", "start()", "begin()"],
  "correct_answer": "main()"
}
```

#### 📚 UNIT_CONCEPTS (Conceptos de unidad)
```json
{
  "type": "unit_concepts",
  "title": "Tipos de datos",
  "points": 10,
  "description": "Conceptos fundamentales de variables en C",
  "concepts": {
    "int": "Tipo de dato entero",
    "float": "Tipo de dato decimal",
    "char": "Tipo de dato carácter",
    "double": "Tipo de dato decimal de doble precisión"
  }
}
```

### 5.2. Sistema de Validación de Ejercicios

#### ✅ COMPLETE & QUESTION
- Comparación directa con `correct_answer`
- Puntos completos si es correcto, 0 si es incorrecto

#### ✅ MAKE_CODE
1. **Compilación**: Se envía a Judge0 API
2. **Ejecución**: Se ejecutan los test_cases
3. **Puntuación**: Proporcional a test_cases pasados
   - Ejemplo: 3/5 test_cases = 60% de puntos

#### ✅ STUDY & UNIT_CONCEPTS
- Automático (solo visualización)
- Puntos completos al completar

### 5.3. Sistema de Puntos y XP

#### Cálculo de Puntos:
```python
# Para ejercicios con validación
points_earned = exercise.points * (correct_tests / total_tests)

# Para ejercicios de estudio
points_earned = exercise.points  # Puntos completos
```

#### XP de Lecciones:
- Cada lección tiene un `xp_reward` fijo
- Se otorga al completar TODOS los ejercicios de la lección
- No es la suma de puntos de ejercicios, es un bonus adicional

---

## 6. SISTEMA DE AUTENTICACIÓN

### 6.1. JWT Token Configuration
- **Algoritmo**: HS256
- **Expiración**: 180 minutos
- **Secret Key**: Configurada en variables de entorno
- **Payload**: 
  ```json
  {
    "sub": "username",
    "role": "student | teacher"
  }
  ```

### 6.2. Roles de Usuario
- **student**: Acceso a contenido, realizar ejercicios, ver progreso
- **teacher**: Todo lo de student + crear/editar módulos, gestionar recompensas

### 6.3. Flujo de Autenticación
```
1. Usuario → POST /users/login (username, password)
2. Backend → Valida credenciales
3. Backend → Genera JWT token
4. Frontend → Almacena token (localStorage/sessionStorage)
5. Frontend → Incluye token en header: Authorization: Bearer <token>
6. Backend → Valida token en cada request protegido
```

### 6.4. Endpoints por Protección

**Sin autenticación:**
- GET /modules/, GET /modules/{id}
- GET /lessons/{id}
- GET /exercises/{id}
- POST /users/register, POST /users/login
- GET /rewards/

**Con autenticación (cualquier rol):**
- GET /users/me
- GET /users/, GET /users/{id}
- POST /progress/exercise
- GET /progress/user/{id}
- POST /sessions/start, PUT /sessions/{id}/end
- GET /sessions/user/{id}
- GET /rewards/user/{id}

**Solo Teachers:**
- POST /modules/, PUT /modules/{id}, DELETE /modules/{id}
- POST /lessons/, PUT /lessons/{id}, DELETE /lessons/{id}
- POST /rewards/, PUT /rewards/{id}, DELETE /rewards/{id}

---

## 7. ESTADO ACTUAL DEL BACKEND

### ✅ COMPLETAMENTE FUNCIONAL

#### **1. Módulos (Núcleo del Sistema)**
---

## 8. FLUJO DE TRABAJO

### 8.1. 🎓 FLUJO DEL PROFESOR

#### Crear un Módulo Completo
```bash
POST /modules/
Authorization: Bearer <teacher_token>

{
  "title": "Introducción a C",
  "description": "Aprende lo básico del lenguaje C",
  "order": 1,
  "estimate_time": 120,
  "lessons": [
    {
      "title": "Variables y Tipos de Datos",
      "description": "Aprende sobre variables",
      "order": 1,
      "xp_reward": 100,
      "exercises": [
        {
          "type": "study",
          "title": "Conceptos de variables",
          "points": 10,
          "flashcards": {
            "int": "Tipo entero",
            "float": "Tipo decimal"
          },
          "order": 1
        },
        {
          "type": "complete",
          "title": "Completa la declaración",
          "points": 20,
          "text": "Para declarar un entero usamos ___",
          "options": ["int", "float", "char"],
          "correct_answer": "int",
          "order": 2
        },
        {
          "type": "make_code",
          "title": "Declara una variable",
          "points": 50,
          "description": "Declara una variable entera llamada 'edad' con valor 25",
          "code": "#include <stdio.h>\nint main() {\n    // Tu código aquí\n    return 0;\n}",
          "test_cases": [
            {
              "input": "",
              "expected_output": "25"
            }
          ],
          "order": 3
        }
      ]
    }
  ]
}
```

#### Editar una Lección o Ejercicio Existente
```bash
PUT /modules/{module_id}
Authorization: Bearer <teacher_token>

{
  "lessons": [
    {
      "_id": "lesson_id_existente",
      "title": "Variables y Tipos de Datos (Actualizado)",
      "xp_reward": 150,  // Aumentar recompensa
      "exercises": [
        {
          "_id": "exercise_id_existente",
          "points": 25  // Solo actualizar puntos
        }
      ]
    }
  ]
}
```

#### Agregar una Lección Nueva a un Módulo
```bash
PUT /modules/{module_id}
Authorization: Bearer <teacher_token>

{
  "lessons": [
    // ... lecciones existentes (con sus _id)
    {
      "title": "Nueva Lección - Arrays",
      "description": "Aprende sobre arreglos",
      "order": 2,
      "xp_reward": 150,
      "exercises": [...]
    }
  ]
}
```

### 8.2. 👨‍🎓 FLUJO DEL ESTUDIANTE

#### 1. Registro e Inicio de Sesión
```bash
# Registro
POST /users/register
{
  "username": "juan123",
  "email": "juan@example.com",
  "password": "password123"
}

# Login
POST /users/login
{
  "username": "juan123",
  "password": "password123"
}
# Response: { "access_token": "...", "token_type": "bearer" }
```

#### 2. Ver Módulos Disponibles
```bash
GET /modules/
# Response: Lista de todos los módulos con lecciones y ejercicios
```

#### 3. Iniciar una Sesión de Estudio
```bash
POST /sessions/start
Authorization: Bearer <token>
{
  "user_id": "user_id",
  "lesson_id": "lesson_id"
}
```

#### 4. Resolver un Ejercicio
```bash
POST /progress/exercise
Authorization: Bearer <token>
{
  "user_id": "user_id",
  "exercise_uuid": "exercise_uuid",
  "lesson_id": "lesson_id",
  "module_id": "module_id",
  "code": "printf(\"Hola Mundo\");",
  "session_id": "session_id"
}
# Response: Validación, puntos ganados, progreso actualizado
```

#### 5. Finalizar Sesión
```bash
PUT /sessions/{session_id}/end
Authorization: Bearer <token>
# Response: Duración, ejercicios completados, streak actualizado
```

#### 6. Ver Mi Progreso
```bash
GET /progress/user/{user_id}
Authorization: Bearer <token>
# Response: Todos los ejercicios intentados, estado, puntos
```

#### 7. Ver Mis Recompensas
```bash
GET /rewards/user/{user_id}
Authorization: Bearer <token>
# Response: Recompensas obtenidas
```

---

## 9. CONSIDERACIONES PARA FRONTEND

### 9.1. 🔐 Manejo de Autenticación

#### Almacenamiento del Token
```typescript
// Después del login
localStorage.setItem('token', response.access_token);
localStorage.setItem('user', JSON.stringify(response.user));
```

#### Configuración de HTTP Client
```typescript
// Angular Interceptor
export class TokenInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler) {
    const token = localStorage.getItem('token');
    if (token) {
      req = req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      });
    }
    return next.handle(req);
  }
}
```

#### Manejo de Expiración
- Token expira en 180 minutos
- Detectar 401 responses
- Redirigir a login si el token expira

### 9.2. 📊 Estructura de Datos Recomendada

#### Interfaces TypeScript Sugeridas
```typescript
export interface Module {
  id: string;
  title: string;
  description: string;
  order: number;
  estimate_time: number;
  lessons: Lesson[];
}

export interface Lesson {
  id: string;
  title: string;
  description: string;
  order: number;
  xp_reward: number;
  exercises: Exercise[];
}

export interface Exercise {
  exercise_uuid: string;
  type: 'study' | 'complete' | 'make_code' | 'question' | 'unit_concepts';
  title: string;
  points: number;
  order: number;
  // Campos específicos según tipo
  flashcards?: Record<string, string>;
  text?: string;
  options?: string[];
  correct_answer?: string;
  description?: string;
  code?: string;
  test_cases?: TestCase[];
  concepts?: Record<string, string>;
}

export interface UserProgress {
  exercise_uuid: string;
  status: 'not_started' | 'in_progress' | 'completed';
  total_points_earned: number;
  is_mastered: boolean;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'student' | 'teacher';
  total_points: number;
  streak: {
    current_days: number;
    last_practice_date: string;
  };
}
```

### 9.3. 🎨 Componentes Sugeridos

#### Para Estudiantes:
- **ModuleListComponent**: Lista de módulos disponibles
- **ModuleDetailComponent**: Detalle de módulo con lecciones
- **LessonViewComponent**: Vista de lección con ejercicios
- **ExerciseComponent**: Wrapper con sub-componentes por tipo:
  - StudyExerciseComponent (flashcards)
  - CompleteExerciseComponent (fill-in-the-blank)
  - CodeExerciseComponent (editor de código)
  - QuestionExerciseComponent (multiple choice)
  - ConceptsExerciseComponent (conceptos)
- **ProgressDashboardComponent**: Dashboard con progreso
- **RewardsComponent**: Galería de recompensas

#### Para Profesores:
- **ModuleEditorComponent**: Crear/editar módulos
- **LessonEditorComponent**: Crear/editar lecciones
- **ExerciseEditorComponent**: Crear/editar ejercicios
- **StudentProgressComponent**: Ver progreso de estudiantes
- **RewardManagerComponent**: Gestionar recompensas

### 9.4. 📡 Servicios Recomendados

```typescript
// auth.service.ts
- login(username, password)
- register(userData)
- logout()
- getCurrentUser()
- isAuthenticated()
- isTeacher()

// content.service.ts
- getModules()
- getModule(id)
- createModule(module)  // Solo teacher
- updateModule(id, module)  // Solo teacher
- deleteModule(id)  // Solo teacher

// progress.service.ts
- submitExercise(exerciseData)
- getUserProgress(userId)

// session.service.ts
- startSession(userId, lessonId)
- endSession(sessionId)
- getUserSessions(userId)

// rewards.service.ts
- getAllRewards()
- getUserRewards(userId)
- createReward(reward)  // Solo teacher
```

### 9.5. 🎯 Estados y Validaciones

#### Estados de Progreso
```typescript
export enum ProgressStatus {
  NOT_STARTED = 'not_started',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed'
}
```

#### Validaciones del Cliente
- Validar formato de email
- Validar longitud de contraseña (mínimo 6 caracteres)
- Validar que el código no esté vacío antes de enviar
- Validar selección de respuestas en ejercicios

#### Manejo de Errores
```typescript
export interface ApiError {
  detail: string;
  status?: number;
}

// Mostrar mensajes de error amigables
const errorMessages = {
  400: 'Datos inválidos, por favor verifica',
  401: 'Sesión expirada, por favor inicia sesión',
  403: 'No tienes permisos para esta acción',
  404: 'Recurso no encontrado',
  500: 'Error del servidor, intenta más tarde'
};
```

### 9.6. 💡 Funcionalidades UX Recomendadas

- **Carga progresiva**: Mostrar loading spinners
- **Feedback inmediato**: Validación en tiempo real
- **Confirmaciones**: Antes de eliminar o cambios importantes
- **Navegación intuitiva**: Breadcrumbs, botones de navegación
- **Progreso visual**: Barras de progreso, badges
- **Editor de código**: Monaco Editor o CodeMirror
- **Gamificación**: Animaciones al ganar puntos/recompensas
- **Responsive**: Mobile-first design

---

## 10. RESUMEN EJECUTIVO

### ✅ Backend COMPLETO para v1.0

**Funcionalidades Implementadas:**
- ✅ CRUD de módulos (con lecciones y ejercicios embebidos)
- ✅ Sistema de autenticación (estudiantes y profesores)
- ✅ Sistema de progreso y XP con puntuación proporcional
- ✅ Sistema de recompensas (CRUD completo + otorgamiento automático)
- ✅ Sistema de sesiones y tracking de streak
- ✅ Validación de ejercicios (AI, Judge0, comparación directa)
- ✅ Protección de endpoints por roles
- ✅ Historial de intentos y progreso detallado

**Arquitectura:**
- ✅ Documentos embebidos (modules → lessons → exercises)
- ✅ Todo se gestiona desde `/modules/` endpoints
- ✅ Alta performance (una sola query para contenido completo)
- ✅ Código limpio y mantenible

**Servicios Integrados:**
- ✅ Judge0 API para compilación de código C
- ✅ Sistema de validación con IA (opcional)
- ✅ bcrypt para seguridad de contraseñas
- ✅ JWT para autenticación stateless

### 🚀 Listo para Frontend

El backend está **100% funcional** para implementar:
- 👨‍🎓 **Vista de estudiante**: Módulos, lecciones, ejercicios, progreso personal, recompensas
- 👨‍🏫 **Panel de profesor**: Crear/editar módulos completos, ver estudiantes, gestionar recompensas
- 📊 **Dashboard**: Estadísticas, progreso, streak, puntos
- 🏆 **Sistema de gamificación**: Puntos, recompensas, racha de días

### 💡 Próximos Pasos Sugeridos

1. **Frontend Angular**:
   - Implementar sistema de autenticación
   - Crear vistas de módulos y lecciones
   - Desarrollar componentes de ejercicios por tipo
   - Implementar dashboard de progreso

2. **Mejoras Opcionales** (v2.0):
   - Analytics y estadísticas avanzadas
   - Sistema de notificaciones
   - Chat o foro entre estudiantes
   - Modo competitivo/rankings
   - Exportar progreso a PDF

3. **Optimizaciones**:
   - Caching de módulos en frontend
   - Paginación si hay muchos módulos
   - Optimización de imágenes/assets
   - Progressive Web App (PWA)

---

## 🎉 CONCLUSIÓN

**Tu arquitectura es EXCELENTE para este proyecto:**
- ✅ Simple y directa
- ✅ Eficiente (menos consultas a BD)
- ✅ Fácil de mantener
- ✅ Escalable para el alcance del proyecto
- ✅ Perfecta para un sistema tipo Duolingo

**El backend está LISTO para producción** 🚀

---

## 📚 RECURSOS ADICIONALES

### Documentación de la API
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### Códigos de Estado HTTP
- **200**: OK - Operación exitosa
- **201**: Created - Recurso creado
- **204**: No Content - Eliminación exitosa
- **400**: Bad Request - Datos inválidos
- **401**: Unauthorized - Token inválido
- **403**: Forbidden - Sin permisos
- **404**: Not Found - Recurso no encontrado
- **500**: Internal Server Error

### Variables de Entorno Necesarias
```env
MONGO_URI=mongodb+srv://...
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=180
TEACHER_SECRET_KEY=your-teacher-secret
JUDGE0_API_KEY=your-judge0-key
```

---

**Documento actualizado**: 25 de diciembre de 2025  
**Versión**: 2.0  
**Autor**: CodeUP Team
