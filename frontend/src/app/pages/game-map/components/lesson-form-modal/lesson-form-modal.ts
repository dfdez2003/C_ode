// frontend/src/app/pages/game-map/components/lesson-form-modal/lesson-form-modal.ts

import { Component, inject, signal, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ContentService } from '../../../../services/content/content';
import { LessonOut, ModuleOut } from '../../../../models/content';

@Component({
  selector: 'app-lesson-form-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './lesson-form-modal.html',
  styleUrl: './lesson-form-modal.css',
})
export class LessonFormModalComponent {
  private contentService = inject(ContentService);

  // ========== INPUTS ==========
  
  public moduleId = input.required<string>();
  public lesson = input<LessonOut | null>(null); // Si existe, es edición; si no, es creación

  // ========== OUTPUTS ==========
  
  public close = output<void>();
  public lessonSaved = output<void>();

  // ========== SIGNALS ==========
  
  public title = signal('');
  public description = signal('');
  public xpReward = signal(50);
  public isPrivate = signal(false);
  public isSubmitting = signal(false);
  public error = signal<string | null>(null);

  // ========== LIFECYCLE ==========

  ngOnInit(): void {
    // Si estamos editando, cargar datos de la lección
    const lessonData = this.lesson();
    if (lessonData) {
      this.title.set(lessonData.title);
      this.description.set(lessonData.description);
      this.xpReward.set(lessonData.xp_reward || 50);
      this.isPrivate.set(lessonData.is_private || false);
    }
  }

  // ========== COMPUTED ==========

  public get isEditing(): boolean {
    return !!this.lesson();
  }

  public get modalTitle(): string {
    return this.isEditing ? '✏️ Editar Lección' : '➕ Crear Nueva Lección';
  }

  // ========== MÉTODOS ==========

  /**
   * Cerrar el modal sin guardar
   */
  onCancel(): void {
    this.close.emit();
  }

  /**
   * Validar y guardar la lección
   */
  onSubmit(): void {
    // Limpiar error previo
    this.error.set(null);

    // Validaciones
    if (!this.title().trim()) {
      this.error.set('El título es requerido');
      return;
    }

    if (this.title().trim().length < 3) {
      this.error.set('El título debe tener al menos 3 caracteres');
      return;
    }

    if (!this.description().trim()) {
      this.error.set('La descripción es requerida');
      return;
    }

    if (this.xpReward() < 10 || this.xpReward() > 1000) {
      this.error.set('La recompensa debe estar entre 10 y 1000 XP');
      return;
    }

    // Guardar
    this.saveLesson();
  }

  /**
   * Enviar petición al backend
   */
  private saveLesson(): void {
    this.isSubmitting.set(true);

    // Obtener el módulo actual para actualizarlo
    this.contentService.getModuleById(this.moduleId()).subscribe({
      next: (module) => {
        const updatedModule = { ...module };
        
        if (this.isEditing) {
          // Modo edición: actualizar lección existente
          const lessonIndex = updatedModule.lessons.findIndex(l => l._id === this.lesson()?._id);
          if (lessonIndex !== -1) {
            updatedModule.lessons[lessonIndex] = {
              ...updatedModule.lessons[lessonIndex],
              title: this.title().trim(),
              description: this.description().trim(),
              xp_reward: this.xpReward(),
              is_private: this.isPrivate()
            };
          }
        } else {
          // Modo creación: agregar nueva lección
          const newLesson: any = {
            title: this.title().trim(),
            description: this.description().trim(),
            xp_reward: this.xpReward(),
            is_private: this.isPrivate(),
            order: updatedModule.lessons.length,
            exercises: []
          };
          updatedModule.lessons.push(newLesson);
        }

        // Enviar actualización al backend
        this.contentService.updateModule(this.moduleId(), updatedModule as any).subscribe({
          next: () => {
            console.log('✅ Lección guardada exitosamente');
            this.isSubmitting.set(false);
            this.lessonSaved.emit();
            this.close.emit();
          },
          error: (err) => {
            const detail = err.error?.detail || 'Error al guardar la lección';
            this.error.set(detail);
            this.isSubmitting.set(false);
            console.error('❌ Error al guardar lección:', err);
          }
        });
      },
      error: (err) => {
        const detail = err.error?.detail || 'Error al cargar el módulo';
        this.error.set(detail);
        this.isSubmitting.set(false);
      }
    });
  }

  /**
   * Eliminar lección (solo en modo edición)
   */
  onDeleteLesson(): void {
    if (!this.isEditing) return;

    const confirmed = confirm(
      `¿Estás seguro de que deseas eliminar la lección "${this.lesson()?.title}"?\n\n` +
      `Esta acción eliminará todos los ejercicios asociados y no se puede deshacer.`
    );

    if (!confirmed) return;

    this.isSubmitting.set(true);

    // Obtener el módulo y eliminar la lección
    this.contentService.getModuleById(this.moduleId()).subscribe({
      next: (module) => {
        const updatedModule = { ...module };
        updatedModule.lessons = updatedModule.lessons.filter(l => l._id !== this.lesson()?._id);

        // Reordenar las lecciones restantes
        updatedModule.lessons.forEach((lesson, index) => {
          lesson.order = index;
        });

        this.contentService.updateModule(this.moduleId(), updatedModule as any).subscribe({
          next: () => {
            console.log('✅ Lección eliminada exitosamente');
            this.isSubmitting.set(false);
            this.lessonSaved.emit();
            this.close.emit();
          },
          error: (err) => {
            const detail = err.error?.detail || 'Error al eliminar la lección';
            this.error.set(detail);
            this.isSubmitting.set(false);
          }
        });
      },
      error: (err) => {
        const detail = err.error?.detail || 'Error al cargar el módulo';
        this.error.set(detail);
        this.isSubmitting.set(false);
      }
    });
  }

  /**
   * Cerrar modal al hacer click en el backdrop
   */
  onBackdropClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-backdrop')) {
      this.onCancel();
    }
  }
}
