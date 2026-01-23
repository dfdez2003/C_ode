// frontend/src/app/services/progress/progress.service.ts

import { Injectable, signal, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environments';
import { firstValueFrom } from 'rxjs';

/**
 * 📦 Interfaces para Progress
 */
export interface ExerciseSubmission {
  session_id: string;
  exercise_uuid: string;
  user_response: any;
  module_id: string;
  lesson_id: string;
}

export interface ProgressResponse {
  is_correct: boolean;
  lesson_finished: boolean;
  points_earned: number;
  current_score?: number;      // Puntaje del intento actual
  total_possible?: number;     // Puntaje máximo posible
  reward_details?: RewardDetails | null;
  xp_bonus?: number;           // NUEVO: XP bonus por recompensas
  achievements_earned?: string[]; // NUEVO: Array de logros ganados
}

export interface RewardDetails {
  total_xp_earned: number;
  lesson_xp: number;
  bonus_xp: number;
  new_level?: number;
  old_level?: number;
  unlocked_rewards?: UnlockedReward[];
  new_achievements?: Achievement[];
}

export interface UnlockedReward {
  id: string;
  name: string;
  description: string;
  icon: string;
  rarity: string;
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  type: string;
}

export interface UserProgressRecord {
  _id: string;
  user_id: string;
  session_id: string;
  exercise_uuid: string;
  module_id: string;
  lesson_id: string;
  attempt_time: string;
  user_response: any;
  score: number;
  status: string;
}

export interface UserProgressSummary {
  user_id: string;
  total_points: number;
  current_streak: number;
  exercises_completed: number;
  lessons_completed: number;
  modules_completed: number;
  last_activity: string;
  level: number;
  xp: number;
}

/**
 * ProgressService - Gestión del Progreso del Usuario
 * 
 * Funcionalidades:
 * - Enviar respuestas de ejercicios al backend
 * - Obtener progreso global del usuario
 * - Obtener resumen de estadísticas
 * - Tracking de ejercicios completados
 */
@Injectable({
  providedIn: 'root'
})
export class ProgressService {
  private http = inject(HttpClient);

  // 🎯 Estado del progreso
  public lastSubmissionResult = signal<ProgressResponse | null>(null);
  public userProgressSummary = signal<UserProgressSummary | null>(null);
  public isSubmitting = signal<boolean>(false);

  // 📍 API Endpoint
  private readonly API_URL = `${environment.apiUrl}/progress`;

  /**
   * 📝 Enviar la respuesta de un ejercicio
   * @param submission - Datos del ejercicio completado
   * @returns ProgressResponse con feedback y recompensas
   */
  async submitExercise(submission: ExerciseSubmission): Promise<ProgressResponse> {
    this.isSubmitting.set(true);

    try {
      const response = await firstValueFrom(
        this.http.post<ProgressResponse>(`${this.API_URL}/exercise`, submission)
      );

      // Actualizar el estado local
      this.lastSubmissionResult.set(response);

      console.log('✅ Ejercicio enviado correctamente:', response);
      
      // Si hay recompensas, mostrar celebración
      if (response.reward_details) {
        this.showRewardNotification(response.reward_details);
      }

      return response;

    } catch (error) {
      console.error('❌ Error al enviar ejercicio:', error);
      
      // Devolver respuesta de error por defecto
      const errorResponse: ProgressResponse = {
        is_correct: false,
        lesson_finished: false,
        points_earned: 0
      };
      
      this.lastSubmissionResult.set(errorResponse);
      throw error;

    } finally {
      this.isSubmitting.set(false);
    }
  }

  /**
   * 📊 Obtener el progreso completo del usuario
   * @param userId - ID del usuario
   * @returns Lista de todos los intentos de ejercicios
   */
  async getUserProgress(userId: string): Promise<UserProgressRecord[]> {
    try {
      const response = await firstValueFrom(
        this.http.get<UserProgressRecord[]>(`${this.API_URL}/user/${userId}`)
      );

      console.log('✅ Progreso del usuario obtenido:', response.length, 'registros');
      return response;

    } catch (error) {
      console.error('❌ Error al obtener progreso del usuario:', error);
      return [];
    }
  }

  /**
   * 📈 Obtener resumen de estadísticas del usuario
   * @param userId - ID del usuario
   * @returns Resumen con puntos, racha, nivel, etc.
   */
  async getUserProgressSummary(userId: string): Promise<UserProgressSummary | null> {
    try {
      const response = await firstValueFrom(
        this.http.get<UserProgressSummary>(`${this.API_URL}/user/${userId}`)
      );

      // Actualizar el estado local
      this.userProgressSummary.set(response);

      console.log('✅ Resumen de progreso obtenido:', response);
      return response;

    } catch (error) {
      console.error('❌ Error al obtener resumen de progreso:', error);
      return null;
    }
  }

  /**
   * 🎯 Obtener progreso de una lección específica
   * @param userId - ID del usuario
   * @param lessonId - ID de la lección
   * @returns Lista de intentos en esa lección
   */
  async getLessonProgress(userId: string, lessonId: string): Promise<UserProgressRecord[]> {
    try {
      const allProgress = await this.getUserProgress(userId);
      return allProgress.filter(record => record.lesson_id === lessonId);
    } catch (error) {
      console.error('❌ Error al obtener progreso de lección:', error);
      return [];
    }
  }

  /**
   * 🔒 Verificar el estado de una lección (si está bloqueada, completada, etc.)
   * @param lessonId - ID de la lección
   * @returns Estado de la lección para el usuario actual
   */
  async getLessonStatus(lessonId: string): Promise<any> {
    try {
      const response = await firstValueFrom(
        this.http.get<any>(`${this.API_URL}/lesson/${lessonId}/status`)
      );

      console.log('✅ Estado de lección obtenido:', response);
      return response;

    } catch (error) {
      console.error('❌ Error al obtener estado de lección:', error);
      // Si falla, asumimos que puede intentar
      return {
        is_locked: false,
        is_completed: false,
        best_score: 0,
        attempt_count: 0,
        can_attempt: true
      };
    }
  }

  /**
   * 📊 Verificar si un ejercicio específico ya fue completado
   * @param userId - ID del usuario
   * @param exerciseUuid - UUID del ejercicio
   * @returns true si el ejercicio fue completado correctamente
   */
  async isExerciseCompleted(userId: string, exerciseUuid: string): Promise<boolean> {
    try {
      const allProgress = await this.getUserProgress(userId);
      
      const exerciseRecord = allProgress.find(
        record => record.exercise_uuid === exerciseUuid && record.status === 'completed'
      );

      return !!exerciseRecord;

    } catch (error) {
      console.error('❌ Error al verificar estado del ejercicio:', error);
      return false;
    }
  }

  /**
   * 📊 Calcular porcentaje de progreso en una lección
   * @param userId - ID del usuario
   * @param lessonId - ID de la lección
   * @param totalExercises - Total de ejercicios en la lección
   * @returns Porcentaje de completitud (0-100)
   */
  async getLessonCompletionPercentage(
    userId: string, 
    lessonId: string, 
    totalExercises: number
  ): Promise<number> {
    try {
      const lessonProgress = await this.getLessonProgress(userId, lessonId);
      
      const completedExercises = lessonProgress.filter(
        record => record.status === 'completed'
      ).length;

      return Math.round((completedExercises / totalExercises) * 100);

    } catch (error) {
      console.error('❌ Error al calcular porcentaje de lección:', error);
      return 0;
    }
  }

  /**
   * 🎉 Mostrar notificación de recompensas
   * @param rewards - Detalles de las recompensas obtenidas
   */
  private showRewardNotification(rewards: RewardDetails): void {
    // Aquí se puede integrar con un sistema de notificaciones/toasts
    console.log('🎉 ¡Recompensas obtenidas!', rewards);

    if (rewards.new_level) {
      console.log(`🆙 ¡Subiste al nivel ${rewards.new_level}!`);
    }

    if (rewards.unlocked_rewards && rewards.unlocked_rewards.length > 0) {
      console.log('🏆 Nuevas recompensas desbloqueadas:', rewards.unlocked_rewards);
    }

    if (rewards.new_achievements && rewards.new_achievements.length > 0) {
      console.log('🏅 Nuevos logros:', rewards.new_achievements);
    }
  }

  /**
   * 🧹 Limpiar el resultado de la última submisión
   */
  clearLastResult(): void {
    this.lastSubmissionResult.set(null);
  }

  /**
   * 🔄 Refrescar el resumen de progreso del usuario actual
   */
  async refreshUserSummary(userId: string): Promise<void> {
    await this.getUserProgressSummary(userId);
  }
}
