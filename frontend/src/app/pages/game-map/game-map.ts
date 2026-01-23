// frontend/src/app/pages/game-map/game-map.ts

import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ContentService } from '../../services/content/content';
import { AuthService } from '../../services/auth/auth';
import { ModuleOut, LessonOut } from '../../models/content';
import { ModuleNodeComponent } from './components/module-node/module-node';
import { StudentPanelComponent } from './components/student-panel/student-panel';
import { ModuleFormModalComponent } from './components/module-form-modal/module-form-modal';
import { LessonFormModalComponent } from '../modules/detail/components/lesson-form-modal/lesson-form-modal';
import { ModuleEditModal } from './components/module-edit-modal/module-edit-modal';

@Component({
  selector: 'app-game-map',
  standalone: true,
  imports: [CommonModule, ModuleNodeComponent, StudentPanelComponent, ModuleFormModalComponent, LessonFormModalComponent, ModuleEditModal],
  templateUrl: './game-map.html',
  styleUrl: './game-map.css',
})
export class GameMapComponent implements OnInit {
  private contentService = inject(ContentService);
  private authService = inject(AuthService);
  private router = inject(Router);

  // ========== SIGNALS ==========
  
  public modules = signal<ModuleOut[]>([]);
  public isLoading = signal(true);
  public error = signal<string | null>(null);
  
  // Detectar si el usuario es profesor
  public isTeacher = signal<boolean>(false);
  
  // Usuario actual
  public currentUser = this.authService.currentUser;

  // Mostrar modal de creación de módulo
  public showModuleFormModal = signal<boolean>(false);

  // Mostrar modal de edición de módulo
  public showModuleEditModal = signal<boolean>(false);
  public moduleToEdit = signal<ModuleOut | null>(null);

  // Mostrar modal de lección (creación/edición)
  public showLessonFormModal = signal<boolean>(false);
  public editingModuleId = signal<string>('');
  public editingLesson = signal<LessonOut | null>(null);

  // ========== LIFECYCLE ==========

  ngOnInit(): void {
    // Detectar rol del usuario
    const user = this.authService.currentUser();
    this.isTeacher.set(user?.role === 'teacher');

    // Cargar módulos
    this.loadModules();
  }

  // ========== MÉTODOS DE CARGA ==========

  public loadModules(): void {
    this.isLoading.set(true);
    this.error.set(null);

    this.contentService.getModules().subscribe({
      next: (data) => {
        this.modules.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        const detail = err.error?.detail || 'No se pudieron cargar los módulos.';
        this.error.set(detail);
        this.isLoading.set(false);
      },
    });
  }

  // ========== MÉTODOS DE NAVEGACIÓN (ESTUDIANTE) ==========

  /**
   * Estudiante hace click en una lección → Navega a resolver ejercicios
   */
  onLessonClickStudent(moduleId: string, lessonId: string): void {
    // Navegar directamente a la vista de ejercicios de la lección
    this.router.navigate(['/lessons', lessonId]);
  }

  // ========== MÉTODOS DE EDICIÓN (PROFESOR) ==========

  /**
   * Profesor hace click en una lección → Ir al editor de ejercicios
   */
  onLessonClickTeacher(moduleId: string, lessonId: string, lessonIndex: number): void {
    // Navegar a la vista de detalle de la lección (que muestra el game-map de ejercicios y el modal)
    this.router.navigate(['/lessons', lessonId]);
  }

  /**
   * Profesor hace click en "Agregar Lección" a un módulo
   */
  onAddLessonToModule(moduleId: string): void {
    // Abrir modal de creación
    this.editingModuleId.set(moduleId);
    this.editingLesson.set(null);
    this.showLessonFormModal.set(true);
  }

  /**
   * Navegar a estadísticas del profesor
   */
  goToTeacherStats(): void {
    this.router.navigate(['/teacher-stats']);
  }

  /**
   * Navegar al dashboard del estudiante
   */
  goToStudentDashboard(): void {
    this.router.navigate(['/student-dashboard']);
  }

  /**
   * Profesor hace click en "Nuevo Módulo"
   */
  onCreateNewModule(): void {
    this.showModuleFormModal.set(true);
  }

  /**
   * Cerrar modal de creación de módulo
   */
  onCloseModuleFormModal(): void {
    this.showModuleFormModal.set(false);
  }

  /**
   * Recargar módulos después de crear uno nuevo
   */
  onModuleCreated(): void {
    this.loadModules();
  }

  /**
   * Cerrar modal de lección
   */
  onCloseLessonFormModal(): void {
    this.showLessonFormModal.set(false);
    this.editingModuleId.set('');
    this.editingLesson.set(null);
  }

  /**
   * Recargar módulos después de guardar una lección
   */
  onLessonSaved(): void {
    this.loadModules();
  }

  /**
   * Profesor hace click en "Editar Módulo"
   */
  onEditModule(moduleId: string): void {
    const module = this.modules().find(m => m._id === moduleId);
    if (module) {
      this.moduleToEdit.set(module);
      this.showModuleEditModal.set(true);
    }
  }

  /**
   * Guardar cambios del módulo editado
   */
  onSaveModuleEdit(updatedMetadata: any): void {
    const module = this.moduleToEdit();
    if (!module) return;

    this.contentService.updateModuleMetadataHTTP(module._id, updatedMetadata).subscribe({
      next: (updatedModule) => {
        // Actualizar el módulo en la lista local
        const currentModules = this.modules();
        const index = currentModules.findIndex(m => m._id === updatedModule._id);
        if (index !== -1) {
          const updated = [...currentModules];
          updated[index] = updatedModule;
          this.modules.set(updated);
        }
        
        alert('✅ Módulo actualizado exitosamente');
        this.showModuleEditModal.set(false);
        this.moduleToEdit.set(null);
      },
      error: (err) => {
        console.error('❌ Error actualizando módulo:', err);
        alert('❌ Error al actualizar el módulo');
      }
    });
  }

  /**
   * Cerrar modal de edición de módulo
   */
  onCloseModuleEditModal(): void {
    this.showModuleEditModal.set(false);
    this.moduleToEdit.set(null);
  }

  /**
   * Profesor hace click en "Eliminar Módulo"
   */
  onDeleteModule(moduleId: string, moduleTitle: string): void {
    const confirmed = confirm(
      `¿Estás seguro de que deseas eliminar el módulo "${moduleTitle}"?\n\n` +
      `Esta acción eliminará todas las lecciones y ejercicios asociados y no se puede deshacer.`
    );

    if (!confirmed) return;

    this.contentService.deleteModule(moduleId).subscribe({
      next: () => {
        alert('✅ Módulo eliminado exitosamente');
        this.loadModules(); // Recargar lista
      },
      error: (err) => {
        alert('❌ Error al eliminar módulo: ' + err.error?.detail);
      }
    });
  }

  // ========== MÉTODOS DE NAVEGACIÓN (PANEL DE ESTUDIANTES) ==========

  /**
   * Profesor hace click en un estudiante → Ver estadísticas
   */
  onViewStudentStats(userId: string): void {
    this.router.navigate(['/admin/stats/user', userId]);
  }
}
