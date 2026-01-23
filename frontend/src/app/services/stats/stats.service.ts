// frontend/src/app/services/stats/stats.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environments';

export interface StudentStats {
  user_id: string;
  username: string;
  email: string;
  total_xp: number;
  streak_days: number;
  lessons_completed: number;
  exercises_completed: number;
  global_progress_percentage?: number;
  global_progress_text?: string;
  last_activity: string | null;
  active_days: string[];
  active_days_count: number;
  modules_progress: {
    [moduleId: string]: {
      lessons_completed: number;
      total_lessons?: number;
      total_score: number;
      best_scores: Array<{
        lesson_id: string;
        score: number;
        total_possible: number;
      }>;
    };
  };
}

export interface AllStudentsStatsResponse {
  total_students: number;
  students: StudentStats[];
}

export interface StudentDetailedProgress {
  user_info: {
    user_id: string;
    username: string;
    email: string;
    total_xp: number;
    streak_days: number;
  };
  modules: Array<{
    module_id: string;
    module_title: string;
    lessons: Array<{
      lesson_id: string;
      lesson_title: string;
      is_completed: boolean;
      best_score: number;
      total_possible: number;
      attempt_count: number;
      last_attempt: string | null;
      exercises: Array<{
        exercise_uuid: string;
        is_correct: boolean;
        points_earned: number;
        attempt_time: string | null;
      }>;
    }>;
  }>;
}

// ========== INTERFACES PARA ESTUDIANTE (MY STATS) ==========

export interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  unlocked: boolean;
}

export interface LessonDetail {
  lesson_id: string;
  lesson_title: string;
  status: 'completed' | 'not_started';
  score: number;
  total_possible: number;
  attempt_count: number;
}

export interface ModuleProgress {
  module_id: string;
  module_title: string;
  total_lessons: number;
  completed_lessons: number;
  total_exercises: number;
  completed_exercises: number;
  progress_percentage: number;
  average_score: number;
  status: 'not_started' | 'in_progress' | 'completed';
  lessons?: LessonDetail[];
}

export interface ActivityDay {
  date: string;
  active: boolean;
  exercises_count: number;
}

export interface NextGoal {
  type: string;
  title: string;
  description: string;
  icon: string;
  target: number | string;
}

export interface MyStatsResponse {
  user_info: {
    username: string;
    email: string;
    role: string;
  };
  stats: {
    total_xp: number;
    level: number;
    level_progress_percentage: number;
    xp_for_next_level: number;
    streak_days: number;
    lessons_completed: number;
    exercises_completed: number;
    exercises_attempted: number;
    perfect_scores: number;
    active_days_count: number;
    last_activity: string | null;
  };
  global_progress_percentage?: number;
  global_progress_text?: string;
  modules_progress: ModuleProgress[];
  badges: Badge[];
  activity_calendar: ActivityDay[];
  motivational_message: string;
  next_goal: NextGoal;
}

@Injectable({
  providedIn: 'root'
})
export class StatsService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/progress`;

  /**
   * Obtiene estadísticas de TODOS los estudiantes (solo profesores)
   */
  getAllStudentsStats(): Observable<AllStudentsStatsResponse> {
    const url = `${this.apiUrl}/stats/all-students`;
    console.log('📊 HTTP GET Request (All Students Stats):', url);
    return this.http.get<AllStudentsStatsResponse>(url);
  }

  /**
   * Obtiene progreso detallado de un estudiante específico (solo profesores)
   */
  getStudentDetailedProgress(studentId: string): Observable<StudentDetailedProgress> {
    const url = `${this.apiUrl}/stats/student/${studentId}`;
    console.log('📊 HTTP GET Request (Student Detailed Progress):', url);
    return this.http.get<StudentDetailedProgress>(url);
  }

  /**
   * Obtiene las estadísticas personales del estudiante actual (estudiantes)
   */
  getMyStats(): Observable<MyStatsResponse> {
    const url = `${this.apiUrl}/stats/my-stats`;
    console.log('📊 HTTP GET Request (My Stats):', url);
    return this.http.get<MyStatsResponse>(url);
  }
}
