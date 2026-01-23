// frontend/src/app/pages/lesson-editor/lesson-editor.ts

import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ContentService } from '../../services/content/content';
import { LessonOut, ExerciseSummary, ModuleOut } from '../../models/content';
import { ExerciseTypeSelectorComponent } from './components/exercise-type-selector/exercise-type-selector';
import { QuestionExerciseFormComponent } from './components/question-exercise-form/question-exercise-form';
import { StudyExerciseFormComponent } from './components/study-exercise-form/study-exercise-form';
import { CompleteExerciseFormComponent } from './components/complete-exercise-form/complete-exercise-form';
import { MakeCodeExerciseFormComponent } from './components/make-code-exercise-form/make-code-exercise-form';
import { UnitConceptsExerciseFormComponent } from './components/unit-concepts-exercise-form/unit-concepts-exercise-form';
import { LessonEditModal } from './components/lesson-edit-modal/lesson-edit-modal';

type ExerciseType = 'study' | 'complete' | 'make_code' | 'question' | 'unit_concepts';

@Component({
  selector: 'app-lesson-editor',
  standalone: true,
  imports: [
    CommonModule, 
    ExerciseTypeSelectorComponent, 
    QuestionExerciseFormComponent,
    StudyExerciseFormComponent,
    CompleteExerciseFormComponent,
    MakeCodeExerciseFormComponent,
    UnitConceptsExerciseFormComponent,
    LessonEditModal
  ],
  templateUrl: './lesson-editor.html',
  styleUrl: './lesson-editor.css',
})
export class LessonEditorComponent implements OnInit {
  private contentService = inject(ContentService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  // ========== SIGNALS ==========
  
  public lesson = signal<LessonOut | null>(null);
  public moduleId = signal<string>('');
  public moduleTitle = signal<string>('');
  public exercises = signal<ExerciseSummary[]>([]);
  public isLoading = signal(true);
  public error = signal<string | null>(null);

  // Modales
  public showTypeSelector = signal(false);
  public showQuestionForm = signal(false);
  public showStudyForm = signal(false);
  public showCompleteForm = signal(false);
  public showMakeCodeForm = signal(false);
  public showUnitConceptsForm = signal(false);
  public editingExerciseIndex = signal<number | null>(null);
  public showLessonEditModal = signal(false);

  // ========== LIFECYCLE ==========

  ngOnInit(): void {
    // Obtener parámetros de la ruta
    const moduleId = this.route.snapshot.queryParamMap.get('moduleId');
    const lessonId = this.route.snapshot.queryParamMap.get('lessonId');

    if (!moduleId || !lessonId) {
      this.error.set('Parámetros de ruta inválidos');
      this.isLoading.set(false);
      return;
    }

    this.moduleId.set(moduleId);
    this.loadLesson(moduleId, lessonId);
  }

  // ========== MÉTODOS DE CARGA ==========

  /**
   * Cargar la lección y sus ejercicios
   */
  private loadLesson(moduleId: string, lessonId: string): void {
    this.isLoading.set(true);
    this.error.set(null);

    this.contentService.getModuleById(moduleId).subscribe({
      next: (module) => {
        const lesson = module.lessons.find(l => l._id === lessonId);
        
        if (!lesson) {
          this.error.set('Lección no encontrada');
          this.isLoading.set(false);
          return;
        }

        this.lesson.set(lesson);
        this.moduleTitle.set(module.title);
        this.exercises.set(lesson.exercises || []);
        this.isLoading.set(false);
        
        console.log('✅ Lección cargada:', lesson.title);
        console.log('📝 Ejercicios:', this.exercises().length);
      },
      error: (err) => {
        const detail = err.error?.detail || 'Error al cargar la lección';
        this.error.set(detail);
        this.isLoading.set(false);
        console.error('❌ Error:', err);
      }
    });
  }

  // ========== NAVEGACIÓN ==========

  /**
   * Volver al mapa de juego
   */
  public goBack(): void {
    this.router.navigate(['/game-map']);
  }

  // ========== MÉTODOS DE EDICIÓN ==========

  /**
   * Editar información básica de la lección
   */
  public onEditLessonInfo(): void {
    this.showLessonEditModal.set(true);
  }

  /**
   * Cerrar modal de edición de lección
   */
  public onCloseLessonEditModal(): void {
    this.showLessonEditModal.set(false);
  }

  /**
   * Guardar cambios de la lección
   */
  public onSaveLessonEdit(updatedLesson: any): void {
    const lesson = this.lesson();
    if (!lesson) return;

    console.log('💾 Guardando cambios de lección:', updatedLesson);

    this.contentService.updateLessonInModuleHTTP(
      this.moduleId(),
      lesson._id,
      updatedLesson
    ).subscribe({
      next: (module: ModuleOut) => {
        console.log('✅ Lección actualizada:', module);
        
        // Encontrar la lección actualizada en el módulo
        const updatedLessonData = module.lessons.find(l => l._id === lesson._id);
        if (updatedLessonData) {
          this.lesson.set(updatedLessonData);
          alert('✅ Lección actualizada exitosamente');
        }
        
        this.showLessonEditModal.set(false);
      },
      error: (err) => {
        console.error('❌ Error actualizando lección:', err);
        alert('❌ Error al actualizar la lección. Revisa la consola.');
      }
    });
  }

  /**
   * Agregar nuevo ejercicio
   */
  public onAddExercise(): void {
    this.editingExerciseIndex.set(null);
    this.showTypeSelector.set(true);
  }

  /**
   * Manejar selección de tipo de ejercicio
   */
  public onTypeSelected(type: ExerciseType): void {
    this.showTypeSelector.set(false);
    
    // Abrir el formulario correspondiente
    switch(type) {
      case 'question':
        this.showQuestionForm.set(true);
        break;
      case 'study':
        this.showStudyForm.set(true);
        break;
      case 'complete':
        this.showCompleteForm.set(true);
        break;
      case 'make_code':
        this.showMakeCodeForm.set(true);
        break;
      case 'unit_concepts':
        this.showUnitConceptsForm.set(true);
        break;
    }
  }

  /**
   * Editar ejercicio existente
   */
  public onEditExercise(exerciseIndex: number): void {
    const exercise = this.exercises()[exerciseIndex];
    this.editingExerciseIndex.set(exerciseIndex);
    
    // Abrir formulario según el tipo
    switch(exercise.type) {
      case 'question':
        this.showQuestionForm.set(true);
        break;
      case 'study':
        this.showStudyForm.set(true);
        break;
      case 'complete':
        this.showCompleteForm.set(true);
        break;
      case 'make_code':
        this.showMakeCodeForm.set(true);
        break;
      case 'unit_concepts':
        this.showUnitConceptsForm.set(true);
        break;
    }
  }

  /**
   * Guardar ejercicio (crear o actualizar)
   */
  public onSaveExercise(exerciseData: any): void {
    const lesson = this.lesson();
    if (!lesson) return;

    const moduleId = this.moduleId();
    const lessonId = lesson._id;

    console.log('💾 Guardando ejercicio:', exerciseData);

    // Cargar el módulo completo para actualizarlo
    this.contentService.getModuleById(moduleId).subscribe({
      next: (module) => {
        // Clonar el módulo
        const updatedModule = { ...module };
        
        // Encontrar la lección
        const lessonIndex = updatedModule.lessons.findIndex(l => l._id === lessonId);
        if (lessonIndex === -1) {
          alert('❌ Error: Lección no encontrada');
          return;
        }

        // Clonar lección
        const updatedLesson = { ...updatedModule.lessons[lessonIndex] };
        const exercises = [...(updatedLesson.exercises || [])];

        // Crear o actualizar ejercicio
        const editingIndex = this.editingExerciseIndex();
        if (editingIndex !== null) {
          // Actualizar existente
          exercises[editingIndex] = exerciseData;
        } else {
          // Agregar nuevo
          exercises.push(exerciseData);
        }

        // Actualizar ejercicios
        updatedLesson.exercises = exercises;
        updatedModule.lessons[lessonIndex] = updatedLesson;

        // Guardar en backend
        this.contentService.updateModule(moduleId, updatedModule as any).subscribe({
          next: () => {
            // Recargar lección
            this.loadLesson(moduleId, lessonId);
            
            // Cerrar todos los formularios
            this.closeAllForms();
            this.editingExerciseIndex.set(null);
            
            alert('✅ Ejercicio guardado exitosamente');
          },
          error: (err) => {
            const detail = err.error?.detail || 'Error al guardar ejercicio';
            alert(`❌ Error: ${detail}`);
            console.error('❌ Error:', err);
          }
        });
      },
      error: (err) => {
        alert('❌ Error al cargar el módulo');
        console.error('❌ Error:', err);
      }
    });
  }

  /**
   * Cerrar todos los formularios de ejercicios
   */
  private closeAllForms(): void {
    this.showQuestionForm.set(false);
    this.showStudyForm.set(false);
    this.showCompleteForm.set(false);
    this.showMakeCodeForm.set(false);
    this.showUnitConceptsForm.set(false);
  }

  /**
   * Eliminar ejercicio
   */
  public onDeleteExercise(exerciseIndex: number): void {
    const exercise = this.exercises()[exerciseIndex];
    const lesson = this.lesson();
    if (!lesson) return;
    
    const confirmed = confirm(
      `¿Eliminar el ejercicio "${exercise.title}"?\n\nEsta acción no se puede deshacer.`
    );

    if (!confirmed) return;

    const moduleId = this.moduleId();
    const lessonId = lesson._id;

    // Cargar módulo completo
    this.contentService.getModuleById(moduleId).subscribe({
      next: (module) => {
        const updatedModule = { ...module };
        const lessonIndex = updatedModule.lessons.findIndex(l => l._id === lessonId);
        
        if (lessonIndex === -1) {
          alert('❌ Error: Lección no encontrada');
          return;
        }

        const updatedLesson = { ...updatedModule.lessons[lessonIndex] };
        const exercises = [...(updatedLesson.exercises || [])];
        
        // Eliminar ejercicio
        exercises.splice(exerciseIndex, 1);
        
        updatedLesson.exercises = exercises;
        updatedModule.lessons[lessonIndex] = updatedLesson;

        // Guardar
        this.contentService.updateModule(moduleId, updatedModule as any).subscribe({
          next: () => {
            this.loadLesson(moduleId, lessonId);
            alert('✅ Ejercicio eliminado');
          },
          error: (err) => {
            alert(`❌ Error: ${err.error?.detail || 'No se pudo eliminar'}`);
          }
        });
      },
      error: (err) => {
        alert('❌ Error al cargar el módulo');
      }
    });
  }

  /**
   * Mover ejercicio hacia arriba
   */
  public onMoveExerciseUp(exerciseIndex: number): void {
    if (exerciseIndex === 0) return;
    
    // TODO: Implementar reordenamiento
    alert('🚧 Reordenamiento de ejercicios en construcción.');
  }

  /**
   * Mover ejercicio hacia abajo
   */
  public onMoveExerciseDown(exerciseIndex: number): void {
    if (exerciseIndex === this.exercises().length - 1) return;
    
    // TODO: Implementar reordenamiento
    alert('🚧 Reordenamiento de ejercicios en construcción.');
  }

  // ========== HELPERS ==========

  /**
   * Obtener emoji según tipo de ejercicio
   */
  public getExerciseIcon(type: string): string {
    const icons: Record<string, string> = {
      'study': '📚',
      'complete': '✏️',
      'make_code': '💻',
      'question': '❓',
      'unit_concepts': '🧩'
    };
    return icons[type] || '📝';
  }

  /**
   * Obtener nombre legible del tipo de ejercicio
   */
  public getExerciseTypeName(type: string): string {
    const names: Record<string, string> = {
      'study': 'Estudio',
      'complete': 'Completar Código',
      'make_code': 'Escribir Código',
      'question': 'Pregunta',
      'unit_concepts': 'Conceptos'
    };
    return names[type] || type;
  }

  /**
   * Obtener ejercicio para editar (helper para el formulario)
   */
  public getEditingExercise(): any | null {
    const index = this.editingExerciseIndex();
    if (index === null) return null;
    return this.exercises()[index] || null;
  }

  /**
   * Obtener XP del ejercicio (maneja any type)
   */
  public getExerciseXP(exercise: ExerciseSummary): number {
    return (exercise as any).xp_reward || 10;
  }

  /**
   * Obtener cantidad de flashcards (solo para tipo study)
   */
  public getFlashcardsCount(exercise: ExerciseSummary): number {
    return (exercise as any).flashcards?.length || 0;
  }

  /**
   * Obtener respuesta correcta (solo para tipo question)
   */
  public getCorrectAnswer(exercise: ExerciseSummary): string {
    return (exercise as any).correct_answer || '';
  }
}
