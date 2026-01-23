// frontend/src/app/pages/student-dashboard/student-dashboard.ts

import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { StatsService, MyStatsResponse, Badge, ModuleProgress, ActivityDay } from '../../services/stats/stats.service';
import { XPHistoryComponent } from '../../components/xp-history/xp-history';

@Component({
  selector: 'app-student-dashboard',
  standalone: true,
  imports: [CommonModule, XPHistoryComponent],
  templateUrl: './student-dashboard.html',
  styleUrl: './student-dashboard.css',
})
export class StudentDashboardComponent implements OnInit {
  private statsService = inject(StatsService);
  private router = inject(Router);

  // ========== SIGNALS ==========
  
  stats = signal<MyStatsResponse | null>(null);
  isLoading = signal(true);
  error = signal<string | null>(null);

  // ========== LIFECYCLE ==========

  ngOnInit(): void {
    this.loadStats();
  }

  // ========== MÉTODOS DE CARGA ==========

  loadStats(): void {
    this.isLoading.set(true);
    this.error.set(null);

    this.statsService.getMyStats().subscribe({
      next: (data) => {
        this.stats.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        const detail = err.error?.detail || 'No se pudieron cargar tus estadísticas.';
        this.error.set(detail);
        this.isLoading.set(false);
      },
    });
  }

  // ========== MÉTODOS DE NAVEGACIÓN ==========

  goBack(): void {
    this.router.navigate(['/game-map']);
  }

  // ========== MÉTODOS DE UTILIDAD ==========

  /**
   * Obtiene el rango/título del nivel actual
   */
  getLevelTitle(level: number): string {
    if (level >= 20) return 'Maestro Legendario';
    if (level >= 15) return 'Experto Supremo';
    if (level >= 10) return 'Programador Avanzado';
    if (level >= 5) return 'Desarrollador';
    if (level >= 3) return 'Aprendiz Dedicado';
    return 'Novato';
  }

  /**
   * Obtiene el color del nivel
   */
  getLevelColor(level: number): string {
    if (level >= 20) return '#ffd700'; // Dorado
    if (level >= 15) return '#c0c0c0'; // Plateado
    if (level >= 10) return '#cd7f32'; // Bronce
    if (level >= 5) return '#667eea'; // Púrpura
    return '#4ade80'; // Verde
  }

  /**
   * Obtiene el color de intensidad para el calendario
   */
  getActivityIntensity(day: ActivityDay): string {
    if (!day.active) return 'none';
    if (day.exercises_count >= 10) return 'high';
    if (day.exercises_count >= 5) return 'medium';
    return 'low';
  }

  /**
   * Obtiene el mensaje de racha
   */
  getStreakMessage(streak: number): string {
    if (streak === 0) return '¡Empieza hoy!';
    if (streak === 1) return '¡Buen comienzo!';
    if (streak >= 30) return '¡Increíble!';
    if (streak >= 7) return '¡Imparable!';
    return '¡Sigue así!';
  }

  /**
   * Obtiene el ícono del estado del módulo
   */
  getModuleStatusIcon(status: string): string {
    switch (status) {
      case 'completed': return '✅';
      case 'in_progress': return '⏳';
      case 'not_started': return '🔒';
      default: return '📚';
    }
  }

  /**
   * Obtiene el texto del estado del módulo
   */
  getModuleStatusText(status: string): string {
    switch (status) {
      case 'completed': return 'Completado';
      case 'in_progress': return 'En Progreso';
      case 'not_started': return 'No Iniciado';
      default: return '';
    }
  }

  /**
   * Obtiene el color del estado del módulo
   */
  getModuleStatusColor(status: string): string {
    switch (status) {
      case 'completed': return '#10b981';
      case 'in_progress': return '#f59e0b';
      case 'not_started': return '#6b7280';
      default: return '#667eea';
    }
  }
}
