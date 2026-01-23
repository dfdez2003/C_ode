// frontend/src/app/pages/lesson-editor/components/complete-exercise-form/complete-exercise-form.ts

import { Component, inject, signal, input, output, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-complete-exercise-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './complete-exercise-form.html',
  styleUrl: './complete-exercise-form.css',
})
export class CompleteExerciseFormComponent implements OnInit {
  
  // ========== INPUTS ==========
  
  public exercise = input<any | null>(null);
  
  // ========== OUTPUTS ==========
  
  public close = output<void>();
  public save = output<any>();

  // ========== SIGNALS ==========
  
  public title = signal('');
  public codeTemplate = signal('');
  public option1 = signal('');
  public option2 = signal('');
  public option3 = signal('');
  public option4 = signal('');
  public correctOptionIndex = signal(0); // 0, 1, 2, 3
  public xpReward = signal(25);
  public isSubmitting = signal(false);
  public error = signal<string | null>(null);

  // ========== LIFECYCLE ==========

  ngOnInit(): void {
    const ex = this.exercise();
    if (ex) {
      this.title.set(ex.title || '');
      this.codeTemplate.set(ex.text || ex.code_template || '');
      this.xpReward.set(ex.points || ex.xp_reward || 25);
      
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
    return this.isEditing ? '✏️ Editar Completar Código' : '➕ Crear Completar Código';
  }

  // ========== MÉTODOS DEL FORMULARIO ==========

  public onCancel(): void {
    this.close.emit();
  }

  public onSubmit(): void {
    this.error.set(null);

    if (!this.title().trim()) {
      this.error.set('El título es requerido');
      return;
    }

    if (this.title().trim().length < 3) {
      this.error.set('El título debe tener al menos 3 caracteres');
      return;
    }

    if (!this.codeTemplate().trim()) {
      this.error.set('El template de código es requerido');
      return;
    }

    // Verificar que hay espacios en blanco (___) en el template
    if (!this.codeTemplate().includes('___')) {
      this.error.set('El template debe contener al menos un espacio en blanco (___)');
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

    if (this.xpReward() < 10 || this.xpReward() > 100) {
      this.error.set('El XP debe estar entre 10 y 100');
      return;
    }

    const options = [opt1, opt2, opt3, opt4];
    const correctAnswer = options[this.correctOptionIndex()];

    const exerciseData = {
      type: 'complete',
      title: this.title().trim(),
      text: this.codeTemplate().trim(),  // Backend: text = template de código
      options: options,
      correct_answer: correctAnswer,
      xp_reward: this.xpReward()
    };

    this.save.emit(exerciseData);
  }

  public onBackdropClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-backdrop')) {
      this.onCancel();
    }
  }
}
