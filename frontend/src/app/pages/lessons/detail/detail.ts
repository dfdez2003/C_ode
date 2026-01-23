// frontend/src/app/pages/lessons/detail/detail.component.ts

import { Component, Input, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LessonOut, LessonStatus } from '../../../models/content';
import { AuthService } from '../../../services/auth/auth';
import { ProgressService } from '../../../services/progress/progress.service';
import { ContentService } from '../../../services/content/content';
import { ContainerComponent } from '../../exercises/container/container';
import { ExerciseSummary } from '../../../models/content';
import { ExerciseCreatorModalComponent } from './components/exercise-creator-modal/exercise-creator-modal';
import { LessonEditModal } from '../../lesson-editor/components/lesson-edit-modal/lesson-edit-modal';

@Component({
  selector: 'app-lesson-detail',
  standalone: true,
  imports: [CommonModule, ContainerComponent, ExerciseCreatorModalComponent, LessonEditModal],
  templateUrl: './detail.html',
  styleUrl: './detail.css',
})
export class DetailComponent implements OnInit {
  private authService = inject(AuthService);
  private progressService = inject(ProgressService);
  private contentService = inject(ContentService);
  
  // ✨ INPUT CLAVE: Recibe el objeto LessonOut del componente padre (ModuleDetailComponent)
  private _lesson = signal<LessonOut | undefined>(undefined);
  @Input({ required: true }) 
  set lesson(value: LessonOut) {
    console.log('🟢 LessonDetail - Nueva lección recibida:', value._id);
    console.log('🟢 Ejercicios en la lección:', value.exercises.length);
    value.exercises.forEach((ex, idx) => {
      console.log(`🟢 Ejercicio ${idx}:`, ex.type, ex.title);
      if (ex.type === 'study') {
        console.log(`  📚 Flashcards:`, (ex as any).flashcards);
      }
    });
    this._lesson.set(value);
    
    // Verificar estado de la lección
    this.checkLessonStatus();
  }
  get lesson(): LessonOut {
    return this._lesson()!;
  }
  
  @Input() moduleTitle: string = '';
  @Input({ required: true }) moduleId!: string;

  public editingExercise = signal<ExerciseSummary | null>(null);
  public lessonStatus = signal<LessonStatus | null>(null);
  public showConfirmationModal = signal<boolean>(false);
  public showAddExerciseModal = signal<boolean>(false);
  public exerciseToEdit = signal<ExerciseSummary | null>(null); // ✨ NUEVO: ejercicio a editar
  public showEditLessonModal = signal<boolean>(false); // ✨ NUEVO: modal de editar lección
  
  async ngOnInit() {
    console.log('🎯 LessonDetail - ngOnInit');
    console.log('   User Role:', this.userRole);
    console.log('   Module ID:', this.moduleId);
    console.log('   Lesson ID:', this._lesson()?._id);
    await this.checkLessonStatus();
  }
  
  /**
   * Verificar si la lección está bloqueada o completada
   */
  private async checkLessonStatus(): Promise<void> {
    if (!this._lesson()) return;
    
    try {
      const status = await this.progressService.getLessonStatus(this._lesson()!._id);
      this.lessonStatus.set(status);
      
      console.log('📊 Estado de la lección:', status);
      
      // Si es privada, mostrar modal de confirmación antes de empezar
      if (this._lesson()!.is_private && !status.is_locked && status.attempt_count === 0) {
        console.log('⚠️ LECCIÓN PRIVADA DETECTADA - Mostrando advertencia');
      }
    } catch (error) {
      console.error('❌ Error al verificar estado de lección:', error);
    }
  }
  
  /**
   * Confirmar inicio de examen
   */
  public confirmStartExam(): void {
    this.showConfirmationModal.set(false);
  }
  
  /**
   * Cancelar inicio de examen
   */
  public cancelStartExam(): void {
    this.showConfirmationModal.set(false);
    // Regresar a la lista de lecciones
    window.history.back();
  }
  
  // Lógica para cerrar el formulario
  public cancelEdit(): void {
    this.editingExercise.set(null);
  }

  // ========== MODAL DE AGREGAR EJERCICIO ==========
  
  /**
   * Abre el modal de agregar ejercicio
   */
  public openAddExerciseModal(): void {
    console.log('🎨 Abriendo modal de agregar ejercicio');
    console.log('   showAddExerciseModal antes:', this.showAddExerciseModal());
    this.exerciseToEdit.set(null); // Limpiar ejercicio a editar
    this.showAddExerciseModal.set(true);
    console.log('   showAddExerciseModal después:', this.showAddExerciseModal());
  }

  /**
   * Abre el modal para editar un ejercicio existente
   */
  public startEdit(exercise: ExerciseSummary): void {
    console.log('✏️ Abriendo modal de edición para:', exercise.title);
    this.exerciseToEdit.set(exercise);
    this.showAddExerciseModal.set(true);
  }

  /**
   * Cierra el modal de agregar ejercicio
   */
  public closeAddExerciseModal(): void {
    this.showAddExerciseModal.set(false);
  }

  /**
   * Maneja la creación exitosa de un ejercicio
   */
  public onExerciseCreated(): void {
    this.showAddExerciseModal.set(false);
    
    // Recargar el módulo completo para actualizar la lección con el nuevo ejercicio
    this.contentService.getModuleById(this.moduleId).subscribe({
      next: (module) => {
        // Buscar la lección actualizada dentro del módulo
        const updatedLesson = module.lessons.find(l => l._id === this.lesson._id);
        if (updatedLesson) {
          this.lesson = updatedLesson; // Actualizar la lección
          console.log('✅ Lección actualizada con nuevo ejercicio');
        }
      },
      error: (err) => {
        console.error('❌ Error al recargar módulo:', err);
      }
    });
  }

  /**
   * Elimina un ejercicio de la lección
   */
  public deleteExercise(exercise: ExerciseSummary): void {
    const confirmDelete = confirm(
      `¿Estás seguro de que deseas eliminar el ejercicio "${exercise.title}"?\n\nEsta acción no se puede deshacer.`
    );

    if (!confirmDelete) {
      return;
    }

    console.log('🗑️ Eliminando ejercicio:', exercise.exercise_uuid);

    this.contentService.deleteExerciseFromLesson(
      this.moduleId,
      this.lesson._id,
      exercise.exercise_uuid
    ).subscribe({
      next: () => {
        console.log('✅ Ejercicio eliminado exitosamente');
        
        // Recargar el módulo para actualizar la lección
        this.contentService.getModuleById(this.moduleId).subscribe({
          next: (module) => {
            const updatedLesson = module.lessons.find(l => l._id === this.lesson._id);
            if (updatedLesson) {
              this.lesson = updatedLesson;
              console.log('✅ Lección actualizada después de eliminar ejercicio');
            }
          },
          error: (err: any) => {
            console.error('❌ Error al recargar módulo:', err);
          }
        });
      },
      error: (err: any) => {
        console.error('❌ Error al eliminar ejercicio:', err);
        alert('Error al eliminar el ejercicio. Por favor, inténtalo de nuevo.');
      }
    });
  }

  /**
   * Abre el modal para editar la información de la lección
   */
  public openEditLessonModal(): void {
    console.log('📝 Abriendo modal de editar lección');
    this.showEditLessonModal.set(true);
  }

  /**
   * Cierra el modal de editar lección
   */
  public closeEditLessonModal(): void {
    this.showEditLessonModal.set(false);
  }

  /**
   * Guarda los cambios de la lección editada
   */
  public onSaveLessonEdit(updatedLesson: any): void {
    console.log('💾 Guardando cambios de lección:', updatedLesson);

    this.contentService.updateLessonInModuleHTTP(
      this.moduleId,
      this.lesson._id,
      updatedLesson
    ).subscribe({
      next: (module) => {
        console.log('✅ Lección actualizada:', module);
        
        // Encontrar la lección actualizada en el módulo
        const updatedLessonData = module.lessons.find(l => l._id === this.lesson._id);
        if (updatedLessonData) {
          this.lesson = updatedLessonData;
          alert('✅ Lección actualizada exitosamente');
        }
        
        this.showEditLessonModal.set(false);
      },
      error: (err) => {
        console.error('❌ Error actualizando lección:', err);
        alert('❌ Error al actualizar la lección. Revisa la consola.');
      }
    });
  }

  public userRole = this.authService.getStoredUser()?.role || 'student'; // Obtener el rol
}