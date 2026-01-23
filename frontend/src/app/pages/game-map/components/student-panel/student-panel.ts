// frontend/src/app/pages/game-map/components/student-panel/student-panel.ts

import { Component, inject, signal, OnInit, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../../environments/environments';

// Interface temporal para usuarios (después moveremos a models)
interface UserSummary {
  id: string;
  username: string;
  total_points: number;
  email: string;
  role: string;
}

@Component({
  selector: 'app-student-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './student-panel.html',
  styleUrl: './student-panel.css',
})
export class StudentPanelComponent implements OnInit {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  @Output() studentClick = new EventEmitter<string>();

  // ========== SIGNALS ==========
  
  public students = signal<UserSummary[]>([]);
  public isLoading = signal(true);
  public error = signal<string | null>(null);

  // ========== LIFECYCLE ==========

  ngOnInit(): void {
    this.loadStudents();
  }

  // ========== MÉTODOS ==========

  private loadStudents(): void {
    this.isLoading.set(true);
    this.error.set(null);

    // Cargar estudiantes reales desde el backend
    this.http.get<UserSummary[]>(`${this.apiUrl}/users/?role=student`).subscribe({
      next: (data) => {
        // Ordenar por total_points (XP) de mayor a menor
        const sorted = data.sort((a, b) => (b.total_points || 0) - (a.total_points || 0));
        this.students.set(sorted);
        this.isLoading.set(false);
        console.log('✅ Estudiantes cargados:', sorted.length);
      },
      error: (err) => {
        const detail = err.error?.detail || 'No se pudieron cargar los estudiantes';
        this.error.set(detail);
        this.isLoading.set(false);
        console.error('❌ Error al cargar estudiantes:', err);
      }
    });
  }

  /**
   * Handler cuando se hace click en un estudiante
   */
  onStudentClick(userId: string): void {
    this.studentClick.emit(userId);
  }

  /**
   * Obtiene el emoji de posición
   */
  getRankEmoji(index: number): string {
    switch (index) {
      case 0: return '🥇';
      case 1: return '🥈';
      case 2: return '🥉';
      default: return `${index + 1}.`;
    }
  }
}
