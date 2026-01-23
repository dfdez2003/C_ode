// frontend/src/app/services/content/content.service.ts

import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, map } from 'rxjs';
import { environment } from '../../../environments/environments';
import { 
  ModuleOut, 
  ModuleCreate,
  ModuleUpdate,
  LessonOut, 
  LessonCreate,
  LessonUpdate,
  ExerciseCreate,
  ExerciseSubmission, 
  ProgressResponse 
} from '../../models/content';

@Injectable({
  providedIn: 'root',
})
export class ContentService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;
  private activeSessionId: string | null = 'FAKE_SESSION_ID_12345'; // TEMPORAL

  // ========== SIGNALS PARA ESTADO DE EDICIÓN ==========
  
  /**
   * Signal que mantiene el módulo actualmente en edición
   * Se usa en el editor de lecciones para modificar en memoria antes de guardar
   */
  private editingModuleSignal = signal<ModuleOut | null>(null);
  
  /**
   * Signal de solo lectura para componentes
   */
  public editingModule = this.editingModuleSignal.asReadonly();

  // ========== MÉTODOS HTTP - MÓDULOS ==========
  
  /**
   * Obtiene la lista completa de módulos.
   * Endpoint: GET /modules/
   * Esta ruta es pública y no requiere autenticación.
   */
  getModules(): Observable<ModuleOut[]> {
    const url = `${this.apiUrl}/modules/`;
    return this.http.get<ModuleOut[]>(url);
  }

  /**
   * Obtiene un módulo específico por su ID.
   * El resultado incluye la lista de lecciones incrustadas.
   * Endpoint: GET /modules/{module_id}
   * Esta ruta es pública y no requiere autenticación.
   */
  getModuleById(moduleId: string): Observable<ModuleOut> {
    const url = `${this.apiUrl}/modules/${moduleId}`;
    return this.http.get<ModuleOut>(url);
  }

  /**
   * Crea un nuevo módulo.
   * Endpoint: POST /modules/
   * Requiere autenticación y rol de profesor.
   */
  createModule(module: ModuleCreate): Observable<ModuleOut> {
    const url = `${this.apiUrl}/modules/`;
    return this.http.post<ModuleOut>(url, module);
  }

  /**
   * Actualiza un módulo existente (incluyendo lecciones y ejercicios).
   * Endpoint: PUT /modules/{module_id}
   * Requiere autenticación y rol de profesor.
   */
  updateModule(moduleId: string, update: ModuleUpdate): Observable<ModuleOut> {
    const url = `${this.apiUrl}/modules/${moduleId}`;
    return this.http.put<ModuleOut>(url, update);
  }

  /**
   * Elimina un módulo por completo.
   * Endpoint: DELETE /modules/{module_id}
   * Requiere autenticación y rol de profesor.
   */
  deleteModule(moduleId: string): Observable<void> {
    const url = `${this.apiUrl}/modules/${moduleId}`;
    return this.http.delete<void>(url);
  }

  /**
   * Agrega una nueva lección con ejercicios a un módulo existente.
   * Endpoint: PATCH /modules/{module_id}/lessons
   * Requiere autenticación y rol de profesor.
   */
  addLessonToModule(moduleId: string, lesson: LessonCreate): Observable<ModuleOut> {
    const url = `${this.apiUrl}/modules/${moduleId}/lessons`;
    return this.http.patch<ModuleOut>(url, lesson);
  }

  /**
   * Agrega un nuevo ejercicio a una lección existente.
   * Endpoint: PATCH /modules/{module_id}/lessons/{lesson_id}/exercises
   * Requiere autenticación y rol de profesor.
   */
  addExerciseToLesson(moduleId: string, lessonId: string, exercise: ExerciseCreate): Observable<ModuleOut> {
    const url = `${this.apiUrl}/modules/${moduleId}/lessons/${lessonId}/exercises`;
    console.log('🌐 HTTP PATCH Request:');
    console.log('   URL:', url);
    console.log('   Payload:', JSON.stringify(exercise, null, 2));
    return this.http.patch<ModuleOut>(url, exercise);
  }

  /**
   * Elimina un ejercicio de una lección existente.
   * Endpoint: DELETE /modules/{module_id}/lessons/{lesson_id}/exercises/{exercise_uuid}
   * Requiere autenticación y rol de profesor.
   */
  deleteExerciseFromLesson(moduleId: string, lessonId: string, exerciseUuid: string): Observable<ModuleOut> {
    const url = `${this.apiUrl}/modules/${moduleId}/lessons/${lessonId}/exercises/${exerciseUuid}`;
    console.log('🗑️ HTTP DELETE Request:');
    console.log('   URL:', url);
    return this.http.delete<ModuleOut>(url);
  }

  /**
   * Actualiza un ejercicio en una lección existente (HTTP).
   * Endpoint: PATCH /modules/{module_id}/lessons/{lesson_id}/exercises/{exercise_uuid}
   * Requiere autenticación y rol de profesor.
   */
  updateExerciseInLessonHTTP(moduleId: string, lessonId: string, exerciseUuid: string, exercise: any): Observable<ModuleOut> {
    const url = `${this.apiUrl}/modules/${moduleId}/lessons/${lessonId}/exercises/${exerciseUuid}`;
    console.log('✏️ HTTP PATCH Request (Update Exercise):');
    console.log('   URL:', url);
    console.log('   Payload:', JSON.stringify(exercise, null, 2));
    return this.http.patch<ModuleOut>(url, exercise);
  }

  /**
   * Actualiza una lección existente (metadata: title, description, xp_reward, is_private, order).
   * Endpoint: PATCH /modules/{module_id}/lessons/{lesson_id}
   * Requiere autenticación y rol de profesor.
   */
  updateLessonInModuleHTTP(moduleId: string, lessonId: string, lesson: any): Observable<ModuleOut> {
    const url = `${this.apiUrl}/modules/${moduleId}/lessons/${lessonId}`;
    console.log('✏️ HTTP PATCH Request (Update Lesson):');
    console.log('   URL:', url);
    console.log('   Payload:', JSON.stringify(lesson, null, 2));
    return this.http.patch<ModuleOut>(url, lesson);
  }

  /**
   * Actualiza los metadatos de un módulo (title, description, order, estimate_time)
   * sin modificar sus lecciones.
   */
  updateModuleMetadataHTTP(moduleId: string, metadata: any): Observable<ModuleOut> {
    const url = `${this.apiUrl}/modules/${moduleId}`;
    console.log('✏️ HTTP PATCH Request (Update Module Metadata):');
    console.log('   URL:', url);
    console.log('   Payload:', JSON.stringify(metadata, null, 2));
    return this.http.patch<ModuleOut>(url, metadata);
  }

  // ========== MÉTODOS HTTP - LECCIONES ==========

  /**
   * Obtiene todas las lecciones de todos los módulos.
   * Util para dropdowns en formularios y selecciones del docente.
   * Endpoint: GET /modules/ (obtiene todos los módulos con sus lecciones)
   * Esta ruta es pública y no requiere autenticación.
   */
  getLessons(): Observable<LessonOut[]> {
    return this.getModules().pipe(
      tap((modules: ModuleOut[]) => {
        // Extraer todas las lecciones de todos los módulos
      }),
      map((modules: ModuleOut[]) => {
        // Mapear y extraer todas las lecciones
        const allLessons: LessonOut[] = [];
        modules.forEach(module => {
          if (module.lessons && Array.isArray(module.lessons)) {
            allLessons.push(...module.lessons);
          }
        });
        return allLessons;
      })
    );
  }

  /**
   * Obtiene una lección específica por su ID.
   * El resultado incluye la lista de ejercicios incrustados.
   * Endpoint: GET /lessons/{lesson_id}
   * Esta ruta es pública y no requiere autenticación.
   */
  getLessonById(lessonId: string): Observable<LessonOut> {
    const url = `${this.apiUrl}/lessons/${lessonId}`;
    return this.http.get<LessonOut>(url);
  }

  // ========== MÉTODOS DE EDICIÓN EN MEMORIA ==========

  /**
   * Establece el módulo que se está editando actualmente.
   * Hace una copia profunda para evitar mutaciones accidentales.
   */
  setEditingModule(module: ModuleOut): void {
    this.editingModuleSignal.set(structuredClone(module));
  }

  /**
   * Limpia el módulo en edición.
   */
  clearEditingModule(): void {
    this.editingModuleSignal.set(null);
  }

  /**
   * Actualiza la información básica del módulo en edición.
   */
  updateModuleInfo(updates: Partial<ModuleOut>): void {
    const current = this.editingModuleSignal();
    if (!current) {
      throw new Error('No hay módulo en edición');
    }
    this.editingModuleSignal.set({ ...current, ...updates });
  }

  /**
   * Agrega una nueva lección al módulo en edición.
   */
  addLesson(lesson: LessonCreate): void {
    const current = this.editingModuleSignal();
    if (!current) {
      throw new Error('No hay módulo en edición');
    }
    
    // Convertir LessonCreate a LessonOut (simular lo que haría el backend)
    const newLesson: LessonOut = {
      _id: `temp_${Date.now()}`, // ID temporal hasta que se guarde
      module_id: current._id,
      ...lesson,
      exercises: lesson.exercises.map(ex => ({
        exercise_uuid: ex.exercise_uuid || `temp_${Date.now()}_${Math.random()}`,
        type: ex.type,
        title: ex.title,
        points: ex.points
      }))
    };

    this.editingModuleSignal.update(mod => ({
      ...mod!,
      lessons: [...mod!.lessons, newLesson]
    }));
  }

  /**
   * Actualiza una lección existente en el módulo en edición.
   */
  updateLesson(lessonIndex: number, updates: Partial<LessonOut>): void {
    const current = this.editingModuleSignal();
    if (!current) {
      throw new Error('No hay módulo en edición');
    }
    if (lessonIndex < 0 || lessonIndex >= current.lessons.length) {
      throw new Error('Índice de lección inválido');
    }

    this.editingModuleSignal.update(mod => {
      const lessons = [...mod!.lessons];
      lessons[lessonIndex] = { ...lessons[lessonIndex], ...updates };
      return { ...mod!, lessons };
    });
  }

  /**
   * Elimina una lección del módulo en edición.
   */
  removeLesson(lessonIndex: number): void {
    const current = this.editingModuleSignal();
    if (!current) {
      throw new Error('No hay módulo en edición');
    }
    if (lessonIndex < 0 || lessonIndex >= current.lessons.length) {
      throw new Error('Índice de lección inválido');
    }

    this.editingModuleSignal.update(mod => ({
      ...mod!,
      lessons: mod!.lessons.filter((_, idx) => idx !== lessonIndex)
    }));
  }

  /**
   * Agrega un nuevo ejercicio a una lección en el módulo en edición (en memoria).
   */
  addExerciseToLessonInMemory(lessonIndex: number, exercise: ExerciseCreate): void {
    const current = this.editingModuleSignal();
    if (!current) {
      throw new Error('No hay módulo en edición');
    }
    if (lessonIndex < 0 || lessonIndex >= current.lessons.length) {
      throw new Error('Índice de lección inválido');
    }

    // Convertir ExerciseCreate a ExerciseSummary
    const newExercise = {
      exercise_uuid: exercise.exercise_uuid || `temp_${Date.now()}_${Math.random()}`,
      type: exercise.type,
      title: exercise.title,
      points: exercise.points
    };

    this.editingModuleSignal.update(mod => {
      const lessons = [...mod!.lessons];
      lessons[lessonIndex] = {
        ...lessons[lessonIndex],
        exercises: [...lessons[lessonIndex].exercises, newExercise]
      };
      return { ...mod!, lessons };
    });
  }

  /**
   * Actualiza un ejercicio existente en una lección.
   */
  updateExerciseInLesson(
    lessonIndex: number, 
    exerciseIndex: number, 
    updates: Partial<ExerciseCreate>
  ): void {
    const current = this.editingModuleSignal();
    if (!current) {
      throw new Error('No hay módulo en edición');
    }
    if (lessonIndex < 0 || lessonIndex >= current.lessons.length) {
      throw new Error('Índice de lección inválido');
    }
    if (exerciseIndex < 0 || exerciseIndex >= current.lessons[lessonIndex].exercises.length) {
      throw new Error('Índice de ejercicio inválido');
    }

    this.editingModuleSignal.update(mod => {
      const lessons = [...mod!.lessons];
      const exercises = [...lessons[lessonIndex].exercises];
      exercises[exerciseIndex] = { ...exercises[exerciseIndex], ...updates };
      lessons[lessonIndex] = { ...lessons[lessonIndex], exercises };
      return { ...mod!, lessons };
    });
  }

  /**
   * Elimina un ejercicio de una lección.
   */
  removeExerciseFromLesson(lessonIndex: number, exerciseIndex: number): void {
    const current = this.editingModuleSignal();
    if (!current) {
      throw new Error('No hay módulo en edición');
    }
    if (lessonIndex < 0 || lessonIndex >= current.lessons.length) {
      throw new Error('Índice de lección inválido');
    }
    if (exerciseIndex < 0 || exerciseIndex >= current.lessons[lessonIndex].exercises.length) {
      throw new Error('Índice de ejercicio inválido');
    }

    this.editingModuleSignal.update(mod => {
      const lessons = [...mod!.lessons];
      lessons[lessonIndex] = {
        ...lessons[lessonIndex],
        exercises: lessons[lessonIndex].exercises.filter((_, idx) => idx !== exerciseIndex)
      };
      return { ...mod!, lessons };
    });
  }

  /**
   * Guarda todos los cambios del módulo en edición.
   * Hace un PUT completo al backend con todos los datos.
   */
  saveEditingModule(): Observable<ModuleOut> {
    const module = this.editingModuleSignal();
    if (!module) {
      throw new Error('No hay módulo en edición');
    }

    // Preparar el payload para el backend
    const update: ModuleUpdate = {
      title: module.title,
      description: module.description,
      order: module.order,
      estimate_time: module.estimate_time,
      lessons: module.lessons.map(lesson => ({
        _id: lesson._id.startsWith('temp_') ? undefined : lesson._id, // Quitar IDs temporales
        title: lesson.title,
        description: lesson.description,
        order: lesson.order,
        xp_reward: lesson.xp_reward,
        is_private: lesson.is_private,
        exercises: lesson.exercises.map(ex => ({
          exercise_uuid: ex.exercise_uuid.startsWith('temp_') ? undefined : ex.exercise_uuid,
          type: ex.type as any,
          title: ex.title,
          points: ex.points
        }))
      }))
    };

    return this.updateModule(module._id, update).pipe(
      tap(updated => {
        // Actualizar el signal con el módulo guardado
        this.editingModuleSignal.set(updated);
      })
    );
  }

  // ========== MÉTODOS HTTP - PROGRESO ==========
  
  /**
   * ✅ NUEVO: Valida un ejercicio SIN grabar progreso.
   * Se usa para el botón "Ejecutar" en make_code.
   * Endpoint: POST /progress/exercise/validate
   * @param submission - Los datos de la respuesta del usuario.
   */
  validateExercise(submission: ExerciseSubmission): Observable<{is_correct: boolean, code_feedback: any, points: number}> {
    const url = `${this.apiUrl}/progress/exercise/validate`;
    
    if (!this.activeSessionId) {
        throw new Error("No hay una sesión de estudio activa.");
    }

    const payload: ExerciseSubmission = {
      ...submission,
      session_id: this.activeSessionId,
    };

    return this.http.post<{is_correct: boolean, code_feedback: any, points: number}>(url, payload);
  }
  
  /**
   * Registra el intento del usuario en un ejercicio.
   * Endpoint: POST /progress/exercise
   * @param submission - Los datos de la respuesta del usuario.
   */
  submitExercise(submission: ExerciseSubmission): Observable<ProgressResponse> {
    const url = `${this.apiUrl}/progress/exercise`;
    
    // ❗ CRÍTICO: Asegurarse de que el objeto de sesión se incluya.
    if (!this.activeSessionId) {
        // En una aplicación real, se lanzaría un error o se iniciaría una sesión
        throw new Error("No hay una sesión de estudio activa.");
    }

    const payload: ExerciseSubmission = {
      ...submission,
      session_id: this.activeSessionId, // Usamos el ID temporal o real
    };

    return this.http.post<ProgressResponse>(url, payload);
  }
}