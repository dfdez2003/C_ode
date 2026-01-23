import { Component, inject, signal, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ContentService } from '../../../../services/content/content';
import { ModuleCreate, LessonCreate, ExerciseCreate, ExerciseType } from '../../../../models/content';
import { QuestionExerciseFormComponent } from '../../../lesson-editor/components/question-exercise-form/question-exercise-form';
import { StudyExerciseFormComponent } from '../../../lesson-editor/components/study-exercise-form/study-exercise-form';
import { CompleteExerciseFormComponent } from '../../../lesson-editor/components/complete-exercise-form/complete-exercise-form';
import { MakeCodeExerciseFormComponent } from '../../../lesson-editor/components/make-code-exercise-form/make-code-exercise-form';
import { UnitConceptsExerciseFormComponent } from '../../../lesson-editor/components/unit-concepts-exercise-form/unit-concepts-exercise-form';

@Component({
  selector: 'app-module-form-modal',
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
  templateUrl: './module-form-modal.html',
  styleUrl: './module-form-modal.css',
})
export class ModuleFormModalComponent {
  private contentService = inject(ContentService);

  public close = output<void>();
  public moduleCreated = output<void>();

  // Control de pasos
  public currentStep = signal<'module' | 'lesson' | 'exercise-selector' | 'exercise-form' | 'lessons-summary'>('module');

  // Datos del módulo (Paso 1)
  public moduleTitle = signal('');
  public moduleDescription = signal('');

  // Datos de la lección ACTUAL (Paso 2)
  public lessonTitle = signal('');
  public lessonDescription = signal('');
  public lessonXpReward = signal(50);
  public lessonIsPrivate = signal(false);

  // Datos de ejercicios de la lección ACTUAL (Paso 3)
  public exercises = signal<ExerciseCreate[]>([]);
  public selectedExerciseType = signal<ExerciseType | null>(null);
  public editingExerciseIndex = signal<number | null>(null);

  // 🆕 NUEVO: Array de lecciones completas
  public completedLessons = signal<LessonCreate[]>([]);

  // Estados
  public isSubmitting = signal(false);
  public error = signal<string | null>(null);

  onCancel(): void {
    this.close.emit();
  }

  // ======== PASO 1: DATOS DEL MÓDULO ========
  onModuleNext(): void {
    this.error.set(null);

    if (!this.moduleTitle().trim()) {
      this.error.set('El título del módulo es requerido');
      return;
    }

    if (this.moduleTitle().trim().length < 3) {
      this.error.set('El título debe tener al menos 3 caracteres');
      return;
    }

    if (!this.moduleDescription().trim()) {
      this.error.set('La descripción del módulo es requerida');
      return;
    }

    if (this.moduleDescription().trim().length < 10) {
      this.error.set('La descripción debe tener al menos 10 caracteres');
      return;
    }

    this.currentStep.set('lesson');
  }

  // ======== PASO 2: DATOS DE LA LECCIÓN ========
  onLessonNext(): void {
    this.error.set(null);

    if (!this.lessonTitle().trim()) {
      this.error.set('El título de la lección es requerido');
      return;
    }

    if (this.lessonTitle().trim().length < 3) {
      this.error.set('El título debe tener al menos 3 caracteres');
      return;
    }

    if (!this.lessonDescription().trim()) {
      this.error.set('La descripción de la lección es requerida');
      return;
    }

    if (this.lessonDescription().trim().length < 10) {
      this.error.set('La descripción debe tener al menos 10 caracteres');
      return;
    }

    if (this.lessonXpReward() < 1 || this.lessonXpReward() > 500) {
      this.error.set('El XP debe estar entre 1 y 500');
      return;
    }

    this.currentStep.set('exercise-selector');
  }

  onLessonBack(): void {
    this.currentStep.set('module');
  }

  // ======== PASO 3: EJERCICIOS ========
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

    // 🆕 MEJORADO: Volver al selector de ejercicios automáticamente
    // El usuario decidirá si agregar más ejercicios o crear la lección desde ahí
    this.currentStep.set('exercise-selector');
  }

  /**
   * 🆕 NUEVO: Guarda la lección actual en el array y pregunta si crear otra
   */
  private saveCurrentLesson(): void {
    const currentLesson: LessonCreate = {
      title: this.lessonTitle().trim(),
      description: this.lessonDescription().trim(),
      order: this.completedLessons().length, // Auto-incrementar orden
      xp_reward: this.lessonXpReward(),
      is_private: this.lessonIsPrivate(),
      exercises: this.exercises()
    };

    // Agregar al array
    this.completedLessons.set([...this.completedLessons(), currentLesson]);

    console.log(`✅ Lección "${currentLesson.title}" guardada (${currentLesson.exercises.length} ejercicios)`);
    console.log(`📚 Total de lecciones: ${this.completedLessons().length}`);

    // Ir al resumen de lecciones
    this.currentStep.set('lessons-summary');
  }

  /**
   * 🆕 NUEVO: Agregar otra lección
   */
  public addAnotherLesson(): void {
    // Resetear datos de la lección actual
    this.lessonTitle.set('');
    this.lessonDescription.set('');
    this.lessonXpReward.set(50);
    this.lessonIsPrivate.set(false);
    this.exercises.set([]);
    this.editingExerciseIndex.set(null);
    
    // Volver al paso de lección
    this.currentStep.set('lesson');
  }

  /**
   * 🆕 NUEVO: Eliminar una lección del resumen
   */
  public deleteLesson(index: number): void {
    const lessons = this.completedLessons();
    const lessonToDelete = lessons[index];
    
    const confirm = window.confirm(`¿Eliminar la lección "${lessonToDelete.title}"?`);
    if (!confirm) return;

    const updated = lessons.filter((_, i) => i !== index);
    // Re-indexar el orden
    updated.forEach((lesson, i) => lesson.order = i);
    this.completedLessons.set(updated);
  }

  /**
   * Transforma los datos del formulario al formato que espera el backend
   * Cada tipo de ejercicio tiene campos específicos según ExerciseSchema
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
        // QuestionExerciseSchema: description, options, correct_answer
        return {
          ...baseExercise,
          description: formData.question || formData.description || '',
          options: formData.options || [],
          correct_answer: formData.correct_answer || ''
        };

      case 'study':
        // StudyExerciseSchema: flashcards (Dict<string, string>)
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
        // CompleteExerciseSchema: text, options, correct_answer
        return {
          ...baseExercise,
          text: formData.code_template || formData.text || '',
          options: formData.options || [],
          correct_answer: formData.correct_answer || ''
        };

      case 'make_code':
        // MakeCodeExerciseSchema: description, code, solution, test_cases
        return {
          ...baseExercise,
          description: formData.problem_statement || formData.description || '',
          code: formData.starter_code || formData.code || '',
          solution: formData.solution_code || formData.solution || '',
          test_cases: formData.test_cases || []
        };

      case 'unit_concepts':
        // UnitConceptsExerciseSchema: description, concepts (Dict<string, string>)
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
    // Si no hay ejercicios, no permitir retroceder
    if (this.exercises().length === 0) {
      this.error.set('Debes crear al menos 1 ejercicio antes de continuar');
      return;
    }
    this.currentStep.set('lesson');
  }

  closeExerciseForms(): void {
    this.selectedExerciseType.set(null);
    this.editingExerciseIndex.set(null);
  }

  // ======== FINALIZAR: GUARDAR LECCIÓN Y MOSTRAR RESUMEN ========
  onFinalize(): void {
    if (this.exercises().length === 0) {
      this.error.set('Debes crear al menos 1 ejercicio antes de finalizar');
      return;
    }
    // Guardar la lección actual y mostrar resumen
    this.saveCurrentLesson();
  }

  public createCompleteModule(): void {
    this.isSubmitting.set(true);
    this.error.set(null);

    if (this.completedLessons().length === 0) {
      this.error.set('Debes crear al menos una lección');
      this.isSubmitting.set(false);
      return;
    }

    const newModule: ModuleCreate = {
      title: this.moduleTitle().trim(),
      description: this.moduleDescription().trim(),
      order: 0,
      estimate_time: 30,
      lessons: this.completedLessons() // 🆕 NUEVO: Usar todas las lecciones
    };

    console.log('📦 Creando módulo completo:');
    console.log('📚 Módulo:', {
      title: newModule.title,
      description: newModule.description,
      lecciones: newModule.lessons.length
    });
    
    newModule.lessons.forEach((lesson, i) => {
      console.log(`📝 Lección ${i + 1}: "${lesson.title}" (${lesson.exercises.length} ejercicios, ${lesson.xp_reward} XP)`);
    });
    
    console.log('🚀 Enviando al backend...');

    this.contentService.createModule(newModule).subscribe({
      next: () => {
        console.log('✅ Módulo creado exitosamente con todas las lecciones');
        this.isSubmitting.set(false);
        this.moduleCreated.emit();
        this.close.emit();
      },
      error: (err) => {
        console.error('❌ Error completo del backend:', err);
        console.error('📄 Detalles:', err.error);
        
        let detail = 'Error al crear el módulo';
        if (err.error?.detail) {
          if (Array.isArray(err.error.detail)) {
            // Errores de validación de Pydantic
            detail = err.error.detail.map((e: any) => 
              `${e.loc?.join(' → ') || 'Campo'}: ${e.msg}`
            ).join('\n');
          } else if (typeof err.error.detail === 'string') {
            detail = err.error.detail;
          }
        }
        
        this.error.set(detail);
        this.isSubmitting.set(false);
        console.error('❌ Error al crear módulo:', detail);
      }
    });
  }

  onBackdropClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-backdrop')) {
      this.onCancel();
    }
  }
}
