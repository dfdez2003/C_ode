// frontend/src/app/pages/lessons/lesson-page/lesson-page.ts

import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ContentService } from '../../../services/content/content';
import { LessonOut } from '../../../models/content';
import { DetailComponent as LessonDetailComponent } from '../detail/detail';

/**
 * Componente wrapper que carga una lección individual desde la ruta
 * y se la pasa al LessonDetailComponent para renderizar los ejercicios
 */
@Component({
  selector: 'app-lesson-page',
  standalone: true,
  imports: [CommonModule, LessonDetailComponent],
  template: `
    <div class="lesson-page-container">
      @if (isLoading()) {
        <div class="loading">
          <div class="spinner"></div>
          <p>Cargando lección...</p>
        </div>
      }

      @if (error()) {
        <div class="error">
          <h2>❌ Error al cargar la lección</h2>
          <p>{{ error() }}</p>
          <button class="btn btn-secondary" (click)="goBack()">
            ← Volver al mapa
          </button>
        </div>
      }

      @if (lesson() && !isLoading()) {
        <app-lesson-detail
          [lesson]="lesson()!"
          [moduleId]="moduleId()"
          [moduleTitle]="moduleTitle()"
        />
      }
    </div>
  `,
  styles: [`
    .lesson-page-container {
      min-height: 100vh;
      padding: 2rem;
    }

    .loading, .error {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 50vh;
      text-align: center;
    }

    .spinner {
      width: 50px;
      height: 50px;
      border: 4px solid #e2e8f0;
      border-top-color: #3b82f6;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .error h2 {
      color: #ef4444;
      margin-bottom: 1rem;
    }

    .btn {
      margin-top: 1rem;
      padding: 0.75rem 1.5rem;
      border: none;
      border-radius: 0.5rem;
      cursor: pointer;
      font-size: 1rem;
      transition: all 0.2s;
    }

    .btn-secondary {
      background: #64748b;
      color: white;
    }

    .btn-secondary:hover {
      background: #475569;
      transform: translateY(-2px);
    }
  `]
})
export class LessonPageComponent implements OnInit {
  private contentService = inject(ContentService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  public lesson = signal<LessonOut | null>(null);
  public moduleId = signal<string>('');
  public moduleTitle = signal<string>('');
  public isLoading = signal(true);
  public error = signal<string | null>(null);

  ngOnInit(): void {
    // Obtener el ID de la lección desde la ruta
    const lessonId = this.route.snapshot.paramMap.get('id');
    
    if (!lessonId) {
      this.error.set('No se proporcionó un ID de lección válido');
      this.isLoading.set(false);
      return;
    }

    this.loadLesson(lessonId);
  }

  /**
   * Carga la lección y su módulo padre desde el backend
   */
  private loadLesson(lessonId: string): void {
    this.isLoading.set(true);
    this.error.set(null);

    // Primero cargar todos los módulos para encontrar el que contiene esta lección
    this.contentService.getModules().subscribe({
      next: (modules) => {
        // Buscar el módulo que contiene esta lección
        for (const module of modules) {
          const lesson = module.lessons.find(l => l._id === lessonId);
          if (lesson) {
            this.lesson.set(lesson);
            this.moduleId.set(module._id);
            this.moduleTitle.set(module.title);
            this.isLoading.set(false);
            console.log('✅ Lección cargada:', lesson.title);
            return;
          }
        }

        // Si llegamos aquí, no se encontró la lección
        this.error.set('No se encontró la lección solicitada');
        this.isLoading.set(false);
      },
      error: (err) => {
        const detail = err.error?.detail || 'Error al cargar la lección';
        this.error.set(detail);
        this.isLoading.set(false);
        console.error('❌ Error al cargar lección:', err);
      }
    });
  }

  /**
   * Volver al mapa de aprendizaje
   */
  public goBack(): void {
    this.router.navigate(['/game-map']);
  }
}
