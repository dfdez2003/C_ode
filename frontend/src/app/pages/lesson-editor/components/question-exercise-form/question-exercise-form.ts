// frontend/src/app/pages/lesson-editor/components/question-exercise-form/question-exercise-form.ts

import { Component, inject, signal, input, output, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-question-exercise-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './question-exercise-form.html',
  styleUrl: './question-exercise-form.css',
})
export class QuestionExerciseFormComponent implements OnInit {
  
  // ========== INPUTS ==========
  
  public exercise = input<any | null>(null); // Si existe, es edición
  
  // ========== OUTPUTS ==========
  
  public close = output<void>();
  public save = output<any>();

  // ========== SIGNALS ==========
  
  public title = signal('');
  public question = signal('');
  public option1 = signal('');
  public option2 = signal('');
  public option3 = signal('');
  public option4 = signal('');
  public correctOptionIndex = signal(0); // 0, 1, 2, 3
  public xpReward = signal(10);
  public isSubmitting = signal(false);
  public error = signal<string | null>(null);

  // ========== LIFECYCLE ==========

  ngOnInit(): void {
    const ex = this.exercise();
    if (ex) {
      // Modo edición: cargar datos
      this.title.set(ex.title || '');
      this.question.set(ex.question || ex.description || '');
      this.xpReward.set(ex.xp_reward || ex.points || 10);
      
      // Cargar opciones si existen
      if (ex.options && Array.isArray(ex.options)) {
        this.option1.set(ex.options[0] || '');
        this.option2.set(ex.options[1] || '');
        this.option3.set(ex.options[2] || '');
        this.option4.set(ex.options[3] || '');
      }
      
      // Determinar cuál opción es la correcta
      if (ex.correct_answer) {
        const correctIdx = ex.options?.indexOf(ex.correct_answer);
        if (correctIdx >= 0) {
          this.correctOptionIndex.set(correctIdx);
        }
      }
    }
  }

  // ========== COMPUTED ==========

  public get isEditing(): boolean {
    return !!this.exercise();
  }

  public get modalTitle(): string {
    return this.isEditing ? '✏️ Editar Pregunta' : '➕ Crear Pregunta';
  }

  // ========== MÉTODOS ==========

  /**
   * Cerrar modal sin guardar
   */
  public onCancel(): void {
    this.close.emit();
  }

  /**
   * Validar y guardar
   */
  public onSubmit(): void {
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

    if (!this.question().trim()) {
      this.error.set('La pregunta es requerida');
      return;
    }

    // Validar que las 4 opciones estén completas
    const opt1 = this.option1().trim();
    const opt2 = this.option2().trim();
    const opt3 = this.option3().trim();
    const opt4 = this.option4().trim();

    if (!opt1 || !opt2 || !opt3 || !opt4) {
      this.error.set('Las 4 opciones son obligatorias (1 correcta + 3 incorrectas)');
      return;
    }

    if (this.xpReward() < 5 || this.xpReward() > 100) {
      this.error.set('El XP debe estar entre 5 y 100');
      return;
    }

    const options = [opt1, opt2, opt3, opt4];
    const correctAnswer = options[this.correctOptionIndex()];

    // Crear objeto del ejercicio
    const exerciseData = {
      type: 'question',
      title: this.title().trim(),
      question: this.question().trim(),
      options: options,
      correct_answer: correctAnswer,
      xp_reward: this.xpReward()
    };

    this.save.emit(exerciseData);
  }

  /**
   * Cerrar al hacer click en backdrop
   */
  public onBackdropClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-backdrop')) {
      this.onCancel();
    }
  }
}
