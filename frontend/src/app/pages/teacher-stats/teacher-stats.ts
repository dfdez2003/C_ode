// frontend/src/app/pages/teacher-stats/teacher-stats.ts
import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { StatsService, StudentStats } from '../../services/stats/stats.service';
import { AuthService } from '../../services/auth/auth';

@Component({
  selector: 'app-teacher-stats',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './teacher-stats.html',
  styleUrl: './teacher-stats.css',
})
export class TeacherStatsComponent implements OnInit {
  private statsService = inject(StatsService);
  private authService = inject(AuthService);
  private router = inject(Router);

  // Signals
  public students = signal<StudentStats[]>([]);
  public isLoading = signal(true);
  public error = signal<string | null>(null);
  public selectedStudent = signal<StudentStats | null>(null);

  // Filtros y ordenamiento
  public searchTerm = signal('');
  public sortBy = signal<'xp' | 'streak' | 'lessons' | 'name'>('xp');
  public sortDirection = signal<'asc' | 'desc'>('desc');

  ngOnInit(): void {
    // Verificar que el usuario sea profesor
    const user = this.authService.currentUser();
    if (!user || user.role !== 'teacher') {
      this.router.navigate(['/game-map']);
      return;
    }

    this.loadStats();
  }

  loadStats(): void {
    this.isLoading.set(true);
    this.error.set(null);

    this.statsService.getAllStudentsStats().subscribe({
      next: (response) => {
        console.log('📊 Estadísticas recibidas:', response);
        // Debug: mostrar global_progress_percentage para cada estudiante
        response.students.forEach(student => {
          console.log(`Student: ${student.username}, Global Progress: ${student.global_progress_percentage}`);
        });
        this.students.set(response.students);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('❌ Error al cargar estadísticas:', err);
        this.error.set('Error al cargar las estadísticas de los estudiantes');
        this.isLoading.set(false);
      }
    });
  }

  /**
   * Filtra estudiantes por nombre o email
   */
  getFilteredStudents(): StudentStats[] {
    let filtered = this.students();
    
    // Aplicar búsqueda
    const search = this.searchTerm().toLowerCase();
    if (search) {
      filtered = filtered.filter(s => 
        s.username.toLowerCase().includes(search) ||
        s.email.toLowerCase().includes(search)
      );
    }

    // Aplicar ordenamiento
    const sortBy = this.sortBy();
    const direction = this.sortDirection() === 'asc' ? 1 : -1;

    filtered = [...filtered].sort((a, b) => {
      let compareA: any;
      let compareB: any;

      switch (sortBy) {
        case 'xp':
          compareA = a.total_xp;
          compareB = b.total_xp;
          break;
        case 'streak':
          compareA = a.streak_days;
          compareB = b.streak_days;
          break;
        case 'lessons':
          compareA = a.lessons_completed;
          compareB = b.lessons_completed;
          break;
        case 'name':
          compareA = a.username.toLowerCase();
          compareB = b.username.toLowerCase();
          break;
        default:
          return 0;
      }

      if (compareA < compareB) return -1 * direction;
      if (compareA > compareB) return 1 * direction;
      return 0;
    });

    return filtered;
  }

  /**
   * Cambia el criterio de ordenamiento
   */
  setSortBy(criteria: 'xp' | 'streak' | 'lessons' | 'name'): void {
    if (this.sortBy() === criteria) {
      // Toggle direction si es el mismo criterio
      this.sortDirection.set(this.sortDirection() === 'asc' ? 'desc' : 'asc');
    } else {
      this.sortBy.set(criteria);
      this.sortDirection.set('desc'); // Default descendente
    }
  }

  /**
   * Calcula total de lecciones completadas
   */
  getTotalLessonsCompleted(): number {
    return this.students().reduce((sum, s) => sum + s.lessons_completed, 0);
  }

  /**
   * Calcula XP total de todos los estudiantes
   */
  getTotalXP(): number {
    return this.students().reduce((sum, s) => sum + s.total_xp, 0);
  }

  /**
   * Cuenta estudiantes con racha activa
   */
  getActiveStreaksCount(): number {
    return this.students().filter(s => s.streak_days > 0).length;
  }

  /**
   * Exponer Object para el template
   */
  Object = Object;

  /**
   * Selecciona un estudiante para ver detalles
   */
  selectStudent(student: StudentStats): void {
    this.selectedStudent.set(student);
  }

  /**
   * Cierra el panel de detalles
   */
  closeDetails(): void {
    this.selectedStudent.set(null);
  }

  /**
   * Formatea una fecha para mostrar
   */
  formatDate(dateString: string | null): string {
    if (!dateString) return 'Nunca';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Hoy';
    if (diffDays === 1) return 'Ayer';
    if (diffDays < 7) return `Hace ${diffDays} días`;
    
    return date.toLocaleDateString('es-ES', { 
      day: 'numeric', 
      month: 'short', 
      year: 'numeric' 
    });
  }

  /**
   * Calcula el progreso promedio del estudiante
   * Ahora usa global_progress_percentage del backend
   */
  getAverageProgress(student: StudentStats): number {
    // Usar el progreso global calculado por el backend
    return Math.round((student.global_progress_percentage || 0) * 10) / 10;
  }

  /**
   * Navega de vuelta al game map
   */
  goBack(): void {
    this.router.navigate(['/game-map']);
  }

  /**
   * Navega a la gestión de recompensas
   */
  goToRewards(): void {
    this.router.navigate(['/rewards-management']);
  }
}
