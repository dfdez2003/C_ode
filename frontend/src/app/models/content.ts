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
  exercises: ExerciseSummary[]; // Lista de ejercicios incrustados [cite: 63]
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