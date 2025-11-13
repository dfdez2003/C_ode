// frontend/src/app/pages/modules/detail/detail.component.ts

import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ContentService } from '../../../services/content/content';
import { ModuleOut } from '../../../models/content';
import { ActivatedRoute, Router, RouterLink } from '@angular/router'; 
import { AuthService } from '../../../services/auth/auth';
import { LessonOut } from '../../../models/content';
import { DetailComponent as LessonDetailComponent } from '../../lessons/detail/detail';


@Component({
  selector: 'app-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, LessonDetailComponent], 
  templateUrl: './detail.html',
  styleUrl: './detail.css',
})
export class DetailComponent implements OnInit {
  private contentService = inject(ContentService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private authService = inject(AuthService); // Inyectar

  public selectedLesson = signal<LessonOut | null>(null);
  public module = signal<ModuleOut | null>(null);
  public isLoading = signal(true);
  public error = signal<string | null>(null);
  
  // Obtener el rol del usuario (Estudiante o Profesor) para controlar la vista
  // public userRole = signal(this.authService.currentUser()?.role || 'student');
  public userRole = signal<'student' | 'teacher'>(this.authService.currentUser()?.role || 'student');

  ngOnInit(): void {
    // Suscribirse a los parámetros de la ruta para obtener el ID
    this.route.paramMap.subscribe(params => {
      const moduleId = params.get('id'); 
      if (moduleId) {
        this.loadModuleDetails(moduleId);
      } else {
        this.error.set('ID de módulo no proporcionado.');
        this.isLoading.set(false);
      }
    });
  }

  private loadModuleDetails(moduleId: string): void {
    this.isLoading.set(true);
    this.error.set(null);
    
    this.contentService.getModuleById(moduleId).subscribe({
      next: (data) => {
        this.module.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        const detail = err.error?.detail || 'No se pudo cargar el módulo.';
        this.error.set(detail);
        this.isLoading.set(false);
      },
    });
  }
  /**
   * Maneja la selección de una lección para mostrar su detalle sin cambiar la ruta.
   */
  selectLesson(lesson: LessonOut): void {
    this.selectedLesson.set(lesson);
  }

  /**
   * Vuelve a la vista de lista de lecciones del módulo o a la lista de módulos.
   */
  goBackToModuleList(): void {
    if (this.selectedLesson()) {
      // Si hay una lección seleccionada, solo ocultarla
      this.selectedLesson.set(null);
    } else {
      // Si no hay lección seleccionada, volver a la lista de módulos
      this.router.navigate(['/dashboard']);
    }
  }
}