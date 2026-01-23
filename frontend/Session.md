# 📋 FLUJO DE SESIÓN Y PROGRESO - LECCIONES

## 🎯 Concepto Principal

Los usuarios completan **sesiones de lecciones** donde:
- No se pueden reintentar ejercicios individuales
- No se muestran respuestas correctas durante la sesión
- El puntaje se calcula al finalizar toda la lección
- Solo se puede reintentar la lección completa

---

## 🔄 Flujo de Sesión

### 1. Inicio de Sesión de Lección
```
Usuario selecciona lección
    ↓
POST /sessions (crea sesión)
    ↓
Frontend recibe:
  - session_id
  - lesson_id
  - exercises[] (lista ordenada)
  - start_time
    ↓
Renderiza primer ejercicio
```

### 2. Durante la Sesión

```
Para cada ejercicio:
  1. Usuario completa ejercicio
  2. Frontend guarda respuesta localmente
  3. NO se valida en tiempo real
  4. NO se muestra si es correcta/incorrecta
  5. Se muestra feedback neutro:
     ✓ Correcto → "¡Bien! Continuando..."
     ✗ Incorrecto → "Respuesta registrada. Continuando..."
  6. Avanza automáticamente al siguiente
```

**IMPORTANTE**: 
- No hay botón "Intentar de Nuevo" en ejercicios individuales
- No se revelan respuestas correctas
- Feedback genérico sin revelar resultado real

### 3. Finalización de Sesión

```
Usuario completa último ejercicio
    ↓
Frontend envía todas las respuestas:
POST /progress/session/{session_id}
{
  "responses": [
    {
      "exercise_id": "...",
      "type": "complete",
      "answer": "interpretado",
      "time_spent": 45
    },
    {
      "exercise_id": "...",
      "type": "question",
      "answer": "opcion_b",
      "time_spent": 30
    },
    ...
  ]
}
    ↓
Backend:
  - Valida todas las respuestas
  - Calcula puntos totales
  - Actualiza progreso del usuario
  - Otorga recompensas si aplica
    ↓
Frontend recibe resultado:
{
  "total_points": 85,
  "max_points": 100,
  "correct_answers": 17,
  "total_exercises": 20,
  "time_spent": 450,
  "rewards_earned": [...],
  "lesson_completed": true
}
    ↓
Muestra pantalla de resultados
```

---

## 📊 Componentes de Ejercicios

### Comportamiento Actualizado

#### ✅ StudyExerciseComponent (Flashcards)
- Usuario ve todas las flashcards
- Hace flip en cada una
- Al ver todas → emite `onComplete`
- **No hay validación** (es solo estudio)

#### ✅ CompleteExerciseComponent (Fill-in-the-blank)
- Usuario selecciona respuesta
- Click en "Verificar Respuesta"
- Muestra feedback genérico:
  - ✓ "¡Bien! Continuando..."
  - ✗ "Respuesta registrada. Continuando..."
- **NO muestra respuesta correcta**
- **NO hay botón "Intentar de Nuevo"**
- Avanza automáticamente (1.5s delay)

#### ⏳ QuestionComponent (Multiple Choice)
- Usuario selecciona opción
- Click en "Verificar Respuesta"
- Mismo feedback genérico que Complete
- **NO muestra respuesta correcta**
- **NO hay botón "Intentar de Nuevo"**
- Avanza automáticamente

#### ⏳ MakeCodeComponent (Code Editor)
- Usuario escribe código
- Click en "Ejecutar y Verificar"
- Se muestra output de ejecución (stdout/stderr)
- Feedback genérico sobre si compiló/ejecutó
- **NO muestra código correcto**
- **NO hay botón "Intentar de Nuevo"**
- Avanza al confirmar

#### ⏳ UnitConceptsComponent
- Usuario marca conceptos como entendidos
- Al marcar todos → emite `onComplete`
- **No hay validación** (es autoevaluación)

---

## 🎨 Feedback Visual durante Sesión

### Estados Permitidos:
1. **Pendiente**: Ejercicio no iniciado
2. **En Progreso**: Usuario está respondiendo
3. **Completado**: Usuario envió respuesta
   - Ícono ✓ o ✗ (pero no revela cuál es correcto)
   - Mensaje genérico
   - Transición automática

### Estados NO Permitidos:
- ❌ "Respuesta Correcta: ..."
- ❌ Botón "Intentar de Nuevo"
- ❌ Comparación con respuesta esperada
- ❌ Puntaje individual del ejercicio

---

## 📝 Estructura de Respuestas

### Frontend guarda localmente:
```typescript
interface ExerciseResponse {
  exercise_id: string;
  type: 'study' | 'complete' | 'question' | 'make_code' | 'unit_concepts';
  answer: any; // Estructura varía según tipo
  time_spent: number; // segundos
  started_at: Date;
  completed_at: Date;
}
```

### Tipos de Respuesta por Ejercicio:

```typescript
// Study (flashcards)
{
  type: 'study',
  answer: {
    cards_viewed: ['concepto1', 'concepto2', ...],
    total_flips: 15
  }
}

// Complete (fill-blank)
{
  type: 'complete',
  answer: 'interpretado' // string seleccionado
}

// Question (multiple choice)
{
  type: 'question',
  answer: 'option_b' // ID de opción seleccionada
}

// Make Code
{
  type: 'make_code',
  answer: {
    code: 'def suma(a, b):\n  return a + b',
    execution_output: '...',
    execution_success: true
  }
}

// Unit Concepts
{
  type: 'unit_concepts',
  answer: {
    concepts_marked: ['concepto1', 'concepto2']
  }
}
```

---

## 🏆 Pantalla de Resultados (Post-Sesión)

### Información a Mostrar:
1. **Resumen General**:
   - Puntos obtenidos / Puntos máximos
   - Porcentaje de aciertos
   - Tiempo total empleado

2. **Desglose por Ejercicio**:
   - ✓/✗ por ejercicio
   - Respuesta del usuario
   - **Respuesta correcta** (ahora sí se muestra)
   - Puntos obtenidos

3. **Recompensas**:
   - Insignias desbloqueadas
   - Niveles alcanzados
   - Streaks mantenidos

4. **Acciones Disponibles**:
   - Continuar a siguiente lección
   - Reintentar esta lección
   - Volver al módulo

---

## 🔐 Backend - Endpoints Relacionados

### Iniciar Sesión
```
POST /sessions
Body: {
  "user_id": "...",
  "lesson_id": "..."
}
Response: {
  "session_id": "...",
  "lesson": { ... },
  "exercises": [ ... ]
}
```

### Finalizar Sesión y Obtener Resultados
```
POST /progress/session/{session_id}
Body: {
  "responses": [ ... ]
}
Response: {
  "total_points": 85,
  "max_points": 100,
  "correct_answers": 17,
  "total_exercises": 20,
  "details": [
    {
      "exercise_id": "...",
      "user_answer": "...",
      "correct_answer": "...",
      "is_correct": true,
      "points_earned": 5
    },
    ...
  ],
  "rewards_earned": [ ... ],
  "lesson_completed": true
}
```

### Obtener Progreso del Usuario
```
GET /progress/user/{user_id}
Response: {
  "lessons_completed": [ ... ],
  "modules_completed": [ ... ],
  "total_points": 1250,
  "level": 3,
  "current_streak": 5
}
```

---

## 🚀 Próximos Pasos de Implementación

### Fase Actual: Componentes de Ejercicios
- ✅ StudyExerciseComponent
- ✅ CompleteExerciseComponent (ajustado para sesión)
- ⏳ QuestionComponent
- ⏳ MakeCodeComponent
- ⏳ UnitConceptsComponent

### Fase Siguiente: Gestor de Sesión
1. **SessionService** (frontend):
   - Crear sesión
   - Gestionar estado de sesión
   - Almacenar respuestas localmente
   - Enviar respuestas al finalizar

2. **SessionContainerComponent**:
   - Progress bar de sesión
   - Navegación entre ejercicios
   - Temporizador (opcional)
   - Botón "Finalizar Sesión"

3. **ResultsComponent**:
   - Mostrar resultados detallados
   - Desglose por ejercicio
   - Recompensas obtenidas
   - Opciones de navegación

---

## 📌 Notas Importantes

### Para Desarrollo:
- Todos los componentes de ejercicios deben emitir `onComplete` sin importar si la respuesta es correcta
- El feedback debe ser genérico durante la sesión
- La validación real ocurre en el backend al finalizar
- El frontend solo almacena y envía respuestas, no las valida

### Para Testing:
- Crear datos de prueba con respuestas correctas/incorrectas mezcladas
- Verificar que NO se muestren respuestas correctas durante sesión
- Verificar que SÍ se muestren en pantalla de resultados
- Probar flujo completo: inicio → ejercicios → finalizar → resultados

### Para UX:
- El feedback genérico no debe frustrar al usuario
- Comunicar claramente que verán resultados al final
- Progress bar visible para saber cuánto falta
- Opción de "Guardar y salir" para sesiones largas (futuro)
