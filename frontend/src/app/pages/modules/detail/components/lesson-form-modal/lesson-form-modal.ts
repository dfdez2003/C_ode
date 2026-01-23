// frontend/src/app/pages/modules/detail/components/lesson-form-modal/lesson-form-modal.ts

import { Component, inject, signal, output, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ContentService } from '../../../../../services/content/content';
import { LessonCreate, ExerciseCreate, ExerciseType } from '../../../../../models/content';
import { QuestionExerciseFormComponent } from '../../../../lesson-editor/components/question-exercise-form/question-exercise-form';
import { StudyExerciseFormComponent } from '../../../../lesson-editor/components/study-exercise-form/study-exercise-form';
import { CompleteExerciseFormComponent } from '../../../../lesson-editor/components/complete-exercise-form/complete-exercise-form';
import { MakeCodeExerciseFormComponent } from '../../../../lesson-editor/components/make-code-exercise-form/make-code-exercise-form';
import { UnitConceptsExerciseFormComponent } from '../../../../lesson-editor/components/unit-concepts-exercise-form/unit-concepts-exercise-form';

@Component({
  selector: 'app-lesson-form-modal',
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
  templateUrl: './lesson-form-modal.html',
  styleUrl: './lesson-form-modal.css',
})
export class LessonFormModalComponent {
  private contentService = inject(ContentService);

  // Input: ID del módulo al que se agregará la lección
  public moduleId = input.required<string>();

  // Outputs
  public close = output<void>();
  public lessonCreated = output<void>();

  // Control de pasos (2 pasos: lesson → exercise-selector → exercise-form)
  public currentStep = signal<'lesson' | 'exercise-selector' | 'exercise-form'>('lesson');

  // Datos de la lección (Paso 1)
  public lessonTitle = signal('');
  public lessonDescription = signal('');
  public lessonXpReward = signal(50);
  public lessonIsPrivate = signal(false);

  // Datos de ejercicios (Paso 2)
  public exercises = signal<ExerciseCreate[]>([]);
  public selectedExerciseType = signal<ExerciseType | null>(null);
  public editingExerciseIndex = signal<number | null>(null);

  // Estados
  public isSubmitting = signal(false);
  public error = signal<string | null>(null);

  onCancel(): void {
    this.close.emit();
  }

  // ======== PASO 1: DATOS DE LA LECCIÓN ========
  onLessonNext(): void {
    console.log('🔍 DEBUG onLessonNext() ejecutado');
    console.log('📝 Título:', this.lessonTitle());
    console.log('📝 Descripción:', this.lessonDescription());
    console.log('📝 XP:', this.lessonXpReward());
    
    this.error.set(null);

    if (!this.lessonTitle().trim()) {
      this.error.set('El título de la lección es requerido');
      console.log('❌ Error: Título vacío');
      return;
    }

    if (this.lessonTitle().trim().length < 3) {
      this.error.set('El título debe tener al menos 3 caracteres');
      console.log('❌ Error: Título muy corto');
      return;
    }

    if (!this.lessonDescription().trim()) {
      this.error.set('La descripción de la lección es requerida');
      console.log('❌ Error: Descripción vacía');
      return;
    }

    if (this.lessonDescription().trim().length < 10) {
      this.error.set('La descripción debe tener al menos 10 caracteres');
      console.log('❌ Error: Descripción muy corta');
      return;
    }

    if (this.lessonXpReward() < 1 || this.lessonXpReward() > 500) {
      this.error.set('El XP debe estar entre 1 y 500');
      console.log('❌ Error: XP fuera de rango');
      return;
    }

    console.log('✅ Todas las validaciones pasaron, cambiando a exercise-selector');
    this.currentStep.set('exercise-selector');
    console.log('🎯 currentStep ahora es:', this.currentStep());
  }

  // ======== PASO 2: EJERCICIOS ========
  onExerciseTypeSelected(type: ExerciseType): void {
    this.selectedExerciseType.set(type);
    this.editingExerciseIndex.set(null);
    this.currentStep.set('exercise-form');
  }

  onExerciseSaved(exerciseData: any): void {
    const current = this.exercises();
    const editingIndex = this.editingExerciseIndex();

    // Transformar datos al formato que espera el backend
    const transformedExercise = this.transformExerciseData(exerciseData);

    if (editingIndex !== null) {
      // Editar ejercicio existente
      const updated = [...current];
      updated[editingIndex] = transformedExercise;
      this.exercises.set(updated);
    } else {
      // Agregar nuevo ejercicio
      this.exercises.set([...current, transformedExercise]);
    }

    this.closeExerciseForms();

    // Preguntar si quiere agregar más ejercicios
    const addMore = confirm('¿Deseas agregar otro ejercicio a esta lección?');
    if (addMore) {
      this.currentStep.set('exercise-selector');
    } else {
      this.addLessonToModule();
    }
  }

  /**
   * Transforma los datos del formulario al formato que espera el backend
   * (Copiado de module-form-modal para mantener consistencia)
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

  onEditExercise(index: number): void {
    const exercise = this.exercises()[index];
    this.selectedExerciseType.set(exercise.type);
    this.editingExerciseIndex.set(index);
    this.currentStep.set('exercise-form');
  }

  onDeleteExercise(index: number): void {
    if (confirm('¿Estás seguro de eliminar este ejercicio?')) {
      const updated = this.exercises().filter((_, i) => i !== index);
      this.exercises.set(updated);
    }
  }

  onExerciseBack(): void {
    this.closeExerciseForms();
    this.currentStep.set('exercise-selector');
  }

  onExerciseSelectorBack(): void {
    // Si no hay ejercicios, volver a datos de lección
    if (this.exercises().length === 0) {
      this.currentStep.set('lesson');
    } else {
      // Si ya hay ejercicios, mostrar advertencia
      const goBack = confirm('Ya has creado ejercicios. ¿Seguro que quieres volver? (No se perderán)');
      if (goBack) {
        this.currentStep.set('lesson');
      }
    }
  }

  closeExerciseForms(): void {
    this.selectedExerciseType.set(null);
    this.editingExerciseIndex.set(null);
  }

  // ======== FINALIZAR: AGREGAR LECCIÓN AL MÓDULO ========
  onFinalize(): void {
    if (this.exercises().length === 0) {
      this.error.set('Debes crear al menos 1 ejercicio antes de finalizar');
      return;
    }
    this.addLessonToModule();
  }

  private addLessonToModule(): void {
    this.isSubmitting.set(true);
    this.error.set(null);

    const lesson: LessonCreate = {
      title: this.lessonTitle().trim(),
      description: this.lessonDescription().trim(),
      order: 0, // El backend puede calcular el orden correcto
      xp_reward: this.lessonXpReward(),
      is_private: this.lessonIsPrivate(),
      exercises: this.exercises()
    };

    console.log('➕ Agregando lección al módulo:', this.moduleId());
    console.log('📝 Lección:', {
      title: lesson.title,
      xp_reward: lesson.xp_reward,
      ejercicios: lesson.exercises.length
    });
    console.log('✏️ Ejercicios:');
    lesson.exercises.forEach((ex, i) => {
      console.log(`  ${i + 1}. [${ex.type}] ${ex.title} (${ex.points} pts)`);
    });

    this.contentService.addLessonToModule(this.moduleId(), lesson).subscribe({
      next: () => {
        console.log('✅ Lección agregada exitosamente al módulo');
        this.isSubmitting.set(false);
        this.lessonCreated.emit();
        this.close.emit();
      },
      error: (err) => {
        console.error('❌ Error completo del backend:', err);
        console.error('📄 Detalles:', err.error);
        
        let detail = 'Error al agregar la lección';
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
        console.error('❌ Error al agregar lección:', detail);
      }
    });
  }

  onBackdropClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-backdrop')) {
      this.onCancel();
    }
  }
}
