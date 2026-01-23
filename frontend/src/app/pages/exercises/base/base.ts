// frontend/src/app/pages/exercises/base/base.component.ts

import { Component, Input, Output, EventEmitter, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ExerciseSummary, StudyExerciseData, CompleteExerciseData, QuestionExerciseData, UnitConceptsExerciseData, MakeCodeExerciseData } from '../../../models/content';
import { ProgressService, ExerciseSubmission, ProgressResponse } from '../../../services/progress/progress.service';

// Importar componentes implementados
import { StudyExerciseComponent } from '../types/study/study';
import { CompleteExerciseComponent } from '../types/complete/complete';
import { QuestionExerciseComponent } from '../types/question/question';
import { UnitConceptsExerciseComponent } from '../types/unit_concepts/unit_concepts';
import { MakeCodeExerciseComponent } from '../types/make-code/make-code';
import { AchievementNotificationComponent } from '../../../components/achievement-notification/achievement-notification';

@Component({
  selector: 'app-exercise-base',
  standalone: true,
  imports: [CommonModule, StudyExerciseComponent, CompleteExerciseComponent, QuestionExerciseComponent, UnitConceptsExerciseComponent, MakeCodeExerciseComponent, AchievementNotificationComponent], 
  templateUrl: './base.html',
  styleUrl: './base.css',
})
export class ExerciseBaseComponent {
  // 🔌 Servicio de progreso
  private progressService = inject(ProgressService);

  // 📥 Inputs - Convertimos a signal para reactividad
  private _exerciseSummary = signal<ExerciseSummary | undefined>(undefined);
  @Input({ required: true }) 
  set exerciseSummary(value: ExerciseSummary) {
    console.log('🔶 Base - Nuevo exerciseSummary recibido:', (value as any).uuid, value.type);
    this._exerciseSummary.set(value);
  }
  get exerciseSummary(): ExerciseSummary {
    return this._exerciseSummary()!;
  }
  
  @Input({ required: true }) sessionId!: string | null;
  @Input({ required: true }) moduleId!: string;
  @Input({ required: true }) lessonId!: string;
  
  // 📤 Outputs
  @Output() onExerciseComplete = new EventEmitter<void>();
  
  // 🎯 Estado del ejercicio
  public isSubmitting = signal<boolean>(false);
  public submissionResult = signal<ProgressResponse | null>(null);
  public showFeedback = signal<boolean>(false);
  public achievementsEarned = signal<string[]>([]);
  
  /**
   * 🔄 Computed signal que reactivamente obtiene los datos del ejercicio
   * Se actualiza automáticamente cuando exerciseSummary cambia
   */
  public exerciseData = computed(() => {
    const summary = this._exerciseSummary();
    if (!summary) return null;
    
    const data = summary as any;
    
    // Para study, necesitamos el objeto flashcards
    if (data.type === 'study') {
      const result = {
        flashcards: data.flashcards || {}
      } as StudyExerciseData;
      console.log('🔶 Base exerciseData computed (study) - UUID:', data.uuid);
      console.log('🔶 Flashcards:', result.flashcards);
      return result;
    }
    
    // Para complete, necesitamos text, options, correct_answer
    if (data.type === 'complete') {
      return {
        text: data.text || '',
        options: data.options || [],
        correct_answer: data.correct_answer || ''
      } as CompleteExerciseData;
    }
    
    // Para question, necesitamos description, options, correct_answer
    if (data.type === 'question') {
      return {
        description: data.description || '',
        options: data.options || [],
        correct_answer: data.correct_answer || ''
      } as QuestionExerciseData;
    }
    
    // Para unit_concepts, necesitamos description, concepts
    if (data.type === 'unit_concepts') {
      return {
        description: data.description || '',
        concepts: data.concepts || {}
      } as UnitConceptsExerciseData;
    }
    
    // Para make_code, necesitamos description, code, solution, test_cases
    if (data.type === 'make_code') {
      return {
        description: data.description || '',
        code: data.code || '',
        solution: data.solution || '',
        test_cases: data.test_cases || []
      } as MakeCodeExerciseData;
    }
    
    // Para otros tipos, retornamos el objeto completo
    return data;
  });
  
  /**
   * 📝 Enviar respuesta del ejercicio al backend
   * @param userResponse - Respuesta del usuario (varía según el tipo de ejercicio)
   */
  async submitExerciseResponse(userResponse: any): Promise<void> {
    // Verificar que tengamos sessionId
    if (!this.sessionId) {
      console.error('❌ No hay sessionId activo');
      alert('Error: No hay sesión activa. Por favor, recarga la página.');
      return;
    }

    // Verificar que el ejercicio tenga exercise_uuid
    const exerciseData = this.exerciseSummary as any;
    if (!exerciseData.exercise_uuid) {
      console.error('❌ El ejercicio no tiene exercise_uuid');
      alert('Error: Ejercicio sin identificador. Por favor, contacta al administrador.');
      return;
    }
    
    // Verificar que userResponse no sea undefined
    if (userResponse === undefined) {
      console.error('❌ userResponse es undefined, no se puede enviar');
      return;
    }

    this.isSubmitting.set(true);
    this.showFeedback.set(false);

    try {
      // Construir el objeto de submisión
      const submission: ExerciseSubmission = {
        session_id: this.sessionId,
        exercise_uuid: exerciseData.exercise_uuid,
        user_response: userResponse,
        module_id: this.moduleId,
        lesson_id: this.lessonId
      };

      console.log('📤 Enviando respuesta:', submission);

      // Enviar al backend
      const result = await this.progressService.submitExercise(submission);

      // Guardar resultado y mostrar feedback
      this.submissionResult.set(result);
      this.showFeedback.set(true);

      // 🏆 Capturar y mostrar logros ganados
      if (result.achievements_earned && result.achievements_earned.length > 0) {
        console.log('🏆 Logros ganados:', result.achievements_earned);
        this.achievementsEarned.set(result.achievements_earned);
      }

      console.log('✅ Respuesta procesada:', result);

      // NO auto-avanzar - El usuario debe hacer clic en "Continuar"
      // La lógica de continuar está en cada componente hijo

    } catch (error) {
      console.error('❌ Error al enviar respuesta:', error);
      alert('Error al procesar tu respuesta. Por favor, intenta de nuevo.');
    } finally {
      this.isSubmitting.set(false);
    }
  }
  
  /**
   * ✅ Maneja la completitud del ejercicio
   * Se llama cuando el componente hijo emite onComplete con los datos de respuesta
   */
  async handleExerciseComplete(userResponse: any): Promise<void> {
    console.log('✅ Ejercicio completado, enviando al backend...');
    console.log('📤 Respuesta del usuario:', userResponse);
    
    // Enviar al backend
    await this.submitExerciseResponse(userResponse);
    
    // ✅ SOLO avanzar automáticamente si NO es make_code
    // make_code espera el click en "Continuar"
    if (this.exerciseSummary.type !== 'make_code') {
      this.onExerciseComplete.emit();
    }
  }

  /**
   * ✅ NUEVO: Manejar el click en "Continuar" de make_code
   */
  handleContinue(): void {
    console.log('➡️ Usuario presionó Continuar, avanzando...');
    this.onExerciseComplete.emit();
  }

  /**
   * 🔄 Reintentar eliminado - Los ejercicios no se reintentan
   * El usuario puede continuar independientemente del resultado
   */
}