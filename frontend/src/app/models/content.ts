// frontend/src/app/models/content.ts

// ===============================================
// 1. EJERCICIO (Estructura incrustada)
// Esta es la estructura que se encuentra dentro de LessonOut.
// Contiene campos comunes de ejercicios.
// ===============================================

/** Tipos de ejercicio definidos por el backend [cite: 63, 64] */
export type ExerciseType = 'study' | 'complete' | 'make_code' | 'question' | 'unit_concepts';

export interface ExerciseSummary {
  exercise_uuid: string;
  type: ExerciseType | string;
  title: string;
  points: number;
}

// ===============================================
// 2. LECCIÓN (Estructura incrustada)
// Se encuentra dentro de ModuleOut.
// ===============================================

export interface LessonOut {
  _id: string; // ObjectId convertido a string
  module_id: string; // Referencia al módulo padre [cite: 64]
  title: string;
  description: string;
  order: number;
  xp_reward: number;
  is_private?: boolean;   // 🆕 True si es una lección privada/examen (un solo intento)
  exercises: ExerciseSummary[]; // Lista de ejercicios incrustados [cite: 63]
}

// 🆕 Estado de progreso de una lección para el usuario
export interface LessonStatus {
  is_locked: boolean;       // True si está bloqueada (examen completado)
  is_completed: boolean;    // True si se completó al menos una vez
  best_score: number;       // Mejor puntaje obtenido
  attempt_count: number;    // Número de intentos realizados
  can_attempt: boolean;     // True si puede intentar la lección
}

// ===============================================
// 3. MÓDULO (Estructura principal)
// Colección principal consumida por la API.
// ===============================================

export interface ModuleOut {
  _id: string; // ObjectId convertido a string
  title: string;
  description: string;
  order: number;
  estimate_time: number;
  lessons: LessonOut[]; // Lista de lecciones incrustadas [cite: 63]
}


// ===============================================
// 4. EJERCICIO DETALLADO (Para la vista individual de ejercicio)
// Este es el modelo completo para el ejercicio (incluye el campo 'data') [cite: 65]
// ===============================================

export interface ExerciseOut {
  id: string;
  lesson_id: string;
  exercise_uuid: string;
  type: string;
  title: string;
  points: number;
  data: any; // El campo 'data' contiene la lógica específica (flashcards, code, etc.) [cite: 65]
}

/**
 * Esquema de entrada para registrar el progreso de un ejercicio.
 * Se envía a POST /progress/exercise.
 */
export interface ExerciseSubmission {
  session_id: string;      // ID de la sesión de estudio activa (CRÍTICO para la racha)
  exercise_uuid: string;   // ID del ejercicio anidado
  user_response: any;      // La respuesta del usuario (string, código, array, etc.)
  module_id: string;       // ID del módulo
  lesson_id: string;       // ID de la lección
}

/**
 * Esquema de salida de la API de progreso.
 * Indica si la respuesta fue correcta y qué recompensa obtuvo.
 */
export interface ProgressResponse {
  is_correct: boolean;
  score_awarded: number;
  new_total_points: number;
  new_streak_days: number;
  current_score?: number;      // Puntaje del intento actual
  total_possible?: number;     // Puntaje máximo posible
  detail: string; // Mensaje de retroalimentación
}

// ===============================================
// 5. INTERFACES ESPECÍFICAS POR TIPO DE EJERCICIO
// ===============================================

/**
 * Ejercicio tipo STUDY (Flashcards)
 * Muestra conceptos con sus definiciones para memorizar
 */
export interface StudyExerciseData {
  flashcards: Record<string, string>; // { "concepto": "definición" }
}

/**
 * Ejercicio tipo COMPLETE (Completar espacios)
 * El usuario debe completar el texto seleccionando la opción correcta
 */
export interface CompleteExerciseData {
  text: string;              // Texto con ___ para completar
  options: string[];         // Opciones disponibles
  correct_answer: string;    // Respuesta correcta
}

/**
 * Ejercicio tipo QUESTION (Opción múltiple)
 * Pregunta con varias opciones de respuesta
 */
export interface QuestionExerciseData {
  description: string;       // La pregunta
  options: string[];         // Opciones de respuesta
  correct_answer: string;    // Respuesta correcta
}

/**
 * Ejercicio tipo MAKE_CODE (Programación)
 * El usuario debe escribir código C que pase los test cases
 */
export interface MakeCodeExerciseData {
  description: string;       // Descripción del problema
  code: string;              // Código inicial/plantilla
  solution?: string;         // Solución (opcional, para teachers)
  test_cases: Array<{
    input: string;
    expected_output: string;
  }>;
}

/**
 * Ejercicio tipo UNIT_CONCEPTS (Conceptos de unidad)
 * Muestra conceptos clave de una unidad temática
 */
export interface UnitConceptsExerciseData {
  description: string;       // Descripción general
  concepts: Record<string, string>; // { "concepto": "definición" }
}

/**
 * Union type para todos los tipos de ejercicio
 */
export type ExerciseData = 
  | StudyExerciseData 
  | CompleteExerciseData 
  | QuestionExerciseData 
  | MakeCodeExerciseData 
  | UnitConceptsExerciseData;

// ===============================================
// 6. INTERFACES PARA CREACIÓN/EDICIÓN (PROFESOR)
// ===============================================

/**
 * Datos para crear un nuevo ejercicio
 */
export interface ExerciseCreate {
  exercise_uuid?: string;  // Opcional, se genera automáticamente si no se provee
  type: ExerciseType;
  title: string;
  points: number;
  // Campos específicos por tipo (se agregan dinámicamente en el formulario)
  flashcards?: Record<string, string>;      // Para 'study'
  text?: string;                            // Para 'complete'
  description?: string;                     // Para 'question', 'make_code', 'unit_concepts'
  options?: string[];                       // Para 'complete', 'question'
  correct_answer?: string;                  // Para 'complete', 'question'
  code?: string;                            // Para 'make_code'
  solution?: string;                        // Para 'make_code'
  test_cases?: Array<{                      // Para 'make_code'
    input: string;
    expected_output: string;
  }>;
  concepts?: Record<string, string>;        // Para 'unit_concepts'
}

/**
 * Datos para crear una nueva lección
 */
export interface LessonCreate {
  title: string;
  description: string;
  order: number;
  xp_reward: number;
  is_private?: boolean;
  exercises: ExerciseCreate[];
}

/**
 * Datos para actualizar una lección existente
 */
export interface LessonUpdate {
  _id?: string;              // Si existe, se mantiene la lección; si no, se crea nueva
  module_id?: string;        // Se agrega automáticamente por el backend
  title?: string;
  description?: string;
  order?: number;
  xp_reward?: number;
  is_private?: boolean;
  exercises?: ExerciseCreate[];
}

/**
 * Datos para crear un nuevo módulo
 */
export interface ModuleCreate {
  title: string;
  description: string;
  order: number;
  estimate_time: number;
  lessons: LessonCreate[];
}

/**
 * Datos para actualizar un módulo existente
 */
export interface ModuleUpdate {
  title?: string;
  description?: string;
  order?: number;
  estimate_time?: number;
  lessons?: LessonUpdate[];
}