// frontend/src/app/pages/lessons/detail/components/exercise-creator-modal/exercise-creator-modal.ts

import { Component, inject, signal, output, input, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ContentService } from '../../../../../services/content/content';
import { ExerciseCreate, ExerciseType } from '../../../../../models/content';
import { QuestionExerciseFormComponent } from '../../../../lesson-editor/components/question-exercise-form/question-exercise-form';
import { StudyExerciseFormComponent } from '../../../../lesson-editor/components/study-exercise-form/study-exercise-form';
import { CompleteExerciseFormComponent } from '../../../../lesson-editor/components/complete-exercise-form/complete-exercise-form';
import { MakeCodeExerciseFormComponent } from '../../../../lesson-editor/components/make-code-exercise-form/make-code-exercise-form';
import { UnitConceptsExerciseFormComponent } from '../../../../lesson-editor/components/unit-concepts-exercise-form/unit-concepts-exercise-form';

@Component({
  selector: 'app-exercise-creator-modal',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule,
    QuestionExerciseFormComponent,
    StudyExerciseFormComponent,
    CompleteExerciseFormComponent,
    MakeCodeExerciseFormComponent,
    UnitConceptsExerciseFormComponent
  ],
  templateUrl: './exercise-creator-modal.html',
  styleUrl: './exercise-creator-modal.css',
})
export class ExerciseCreatorModalComponent {
  private contentService = inject(ContentService);

  // Inputs
  public moduleId = input.required<string>();
  public lessonId = input.required<string>();
  public exerciseToEdit = input<any | null>(null); // ✨ NUEVO: ejercicio a editar

  // Outputs
  public close = output<void>();
  public exerciseCreated = output<void>();

  // Control de vista (selector → formulario)
  public currentView = signal<'selector' | 'form'>('selector');
  public selectedExerciseType = signal<ExerciseType | null>(null);

  // Estados
  public isSubmitting = signal(false);
  public error = signal<string | null>(null);

  constructor() {
    // Efecto para detectar cuando se carga un ejercicio a editar
    effect(() => {
      const exercise = this.exerciseToEdit();
      if (exercise) {
        console.log('📝 Modo edición activado para:', exercise.type, exercise.title);
        console.log('📋 Datos completos del ejercicio:', exercise);
        this.selectedExerciseType.set(exercise.type);
        this.currentView.set('form');
      } else {
        // Modo creación
        this.selectedExerciseType.set(null);
        this.currentView.set('selector');
      }
    });
  }

  /**
   * Verifica si estamos en modo edición
   */
  public isEditMode(): boolean {
    return this.exerciseToEdit() !== null;
  }

  onCancel(): void {
    this.close.emit();
  }

  onExerciseTypeSelected(type: ExerciseType): void {
    this.selectedExerciseType.set(type);
    this.currentView.set('form');
  }

  onBackToSelector(): void {
    this.selectedExerciseType.set(null);
    this.currentView.set('selector');
  }

  onExerciseSaved(exerciseData: any): void {
    this.error.set(null);
    this.isSubmitting.set(true);

    // Transformar datos al formato del backend
    const transformedExercise = this.transformExerciseData(exerciseData);

    const isEdit = this.isEditMode();
    const action = isEdit ? '✏️ Actualizando' : '➕ Agregando';
    
    console.log(`${action} ejercicio en lección:`);
    console.log('  📦 Módulo ID:', this.moduleId());
    console.log('  📝 Lección ID:', this.lessonId());
    console.log('  ✏️ Ejercicio transformado:', JSON.stringify(transformedExercise, null, 2));
    console.log('  🔑 Claves del ejercicio:', Object.keys(transformedExercise));

    // Decidir si crear o actualizar
    const request$ = isEdit
      ? this.contentService.updateExerciseInLessonHTTP(
          this.moduleId(),
          this.lessonId(),
          this.exerciseToEdit()!.exercise_uuid,
          transformedExercise
        )
      : this.contentService.addExerciseToLesson(
          this.moduleId(),
          this.lessonId(),
          transformedExercise
        );

    request$.subscribe({
      next: () => {
        console.log(`✅ Ejercicio ${isEdit ? 'actualizado' : 'agregado'} exitosamente`);
        this.isSubmitting.set(false);
        this.exerciseCreated.emit();
        this.close.emit();
      },
      error: (err: any) => {
        console.error('❌ Error al agregar ejercicio:', err);
        console.error('❌ Error completo:', JSON.stringify(err, null, 2));
        
        let detail = 'Error al agregar el ejercicio';
        if (err.error?.detail) {
          if (Array.isArray(err.error.detail)) {
            detail = err.error.detail.map((e: any) => 
              `${e.loc?.join(' → ') || 'Campo'}: ${e.msg}`
            ).join('\n');
          } else if (typeof err.error.detail === 'string') {
            detail = err.error.detail;
          }
        }
        
        this.error.set(detail);
        this.isSubmitting.set(false);
      }
    });
  }

  /**
   * Transforma los datos del formulario al formato que espera el backend
   * (Misma lógica que lesson-form-modal)
   */
  private transformExerciseData(formData: any): any {
    const type = formData.type;
    const points = formData.xp_reward || formData.points || 10;
    
    const baseExercise = {
      type,
      title: formData.title,
      points
    };

    switch (type) {
      case 'question':
        return {
          ...baseExercise,
          description: formData.question || formData.description || '',
          options: formData.options || [],
          correct_answer: formData.correct_answer || ''
        };

      case 'study':
        let flashcardsObj: Record<string, string> = {};
        if (Array.isArray(formData.flashcards)) {
          formData.flashcards.forEach((card: any, index: number) => {
            const key = card.front || `Concepto ${index + 1}`;
            flashcardsObj[key] = card.back || '';
          });
        } else {
          flashcardsObj = formData.flashcards || {};
        }
        return {
          ...baseExercise,
          flashcards: flashcardsObj
        };

      case 'complete':
        return {
          ...baseExercise,
          text: formData.code_template || formData.text || '',
          options: formData.options || [],
          correct_answer: formData.correct_answer || ''
        };

      case 'make_code':
        return {
          ...baseExercise,
          description: formData.problem_statement || formData.description || '',
          code: formData.starter_code || formData.code || '',
          solution: formData.solution_code || formData.solution || '',
          test_cases: formData.test_cases || []
        };

      case 'unit_concepts':
        let conceptsObj: Record<string, string> = {};
        if (Array.isArray(formData.pairs)) {
          formData.pairs.forEach((pair: any) => {
            if (pair.concept && pair.definition) {
              conceptsObj[pair.concept] = pair.definition;
            }
          });
        } else {
          conceptsObj = formData.concepts || {};
        }
        return {
          ...baseExercise,
          description: formData.description || '',
          concepts: conceptsObj
        };

      default:
        console.error('❌ Tipo de ejercicio desconocido:', type);
        return baseExercise;
    }
  }

  onBackdropClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-backdrop')) {
      this.onCancel();
    }
  }
}
