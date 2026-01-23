// frontend/src/app/pages/lesson-editor/components/make-code-exercise-form/make-code-exercise-form.ts

import { Component, inject, signal, input, output, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-make-code-exercise-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './make-code-exercise-form.html',
  styleUrl: './make-code-exercise-form.css',
})
export class MakeCodeExerciseFormComponent implements OnInit {
  
  // ========== INPUTS ==========
  
  public exercise = input<any | null>(null);
  
  // ========== OUTPUTS ==========
  
  public close = output<void>();
  public save = output<any>();

  // ========== SIGNALS ==========
  
  public title = signal('');
  public problemStatement = signal('');  // Enunciado del problema
  public starterCode = signal('');
  public solutionCode = signal('');
  public testCases = signal('');
  public xpReward = signal(50);
  public isSubmitting = signal(false);
  public error = signal<string | null>(null);

  // ========== LIFECYCLE ==========

  ngOnInit(): void {
    const ex = this.exercise();
    if (ex) {
      this.title.set(ex.title || '');
      // Backend usa "description" para el enunciado del problema
      this.problemStatement.set(ex.description || ex.problem_statement || '');
      // Backend usa "code" para el código inicial
      this.starterCode.set(ex.code || ex.starter_code || '');
      // Backend usa "solution" para el código solución
      this.solutionCode.set(ex.solution || ex.solution_code || '');
      // Backend usa "test_cases" como array
      if (Array.isArray(ex.test_cases)) {
        // Puede ser array de strings o array de objetos {input, expected_output}
        const testCasesStr = ex.test_cases.map((tc: any) => {
          if (typeof tc === 'string') {
            return tc;
          } else if (typeof tc === 'object' && tc !== null) {
            // Objeto con input/expected_output
            return `${tc.input || ''} == ${tc.expected_output || ''}`;
          }
          return '';
        }).filter(Boolean).join('\n');
        this.testCases.set(testCasesStr);
      } else if (typeof ex.test_cases === 'string') {
        this.testCases.set(ex.test_cases);
      } else {
        this.testCases.set('');
      }
      this.xpReward.set(ex.xp_reward || ex.points || 50);
      
      console.log('💻 Make Code cargado:', {
        problem: this.problemStatement(),
        starter: this.starterCode(),
        solution: this.solutionCode(),
        tests: this.testCases()
      });
    }
  }

  // ========== COMPUTED ==========

  public get isEditing(): boolean {
    return !!this.exercise();
  }

  public get modalTitle(): string {
    return this.isEditing ? '✏️ Editar Escribir Código' : '➕ Crear Escribir Código';
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

    if (!this.problemStatement().trim()) {
      this.error.set('El enunciado del problema es requerido');
      return;
    }

    if (!this.solutionCode().trim()) {
      this.error.set('La solución de referencia es requerida');
      return;
    }

    if (this.xpReward() < 30 || this.xpReward() > 100) {
      this.error.set('El XP debe estar entre 30 y 100');
      return;
    }

    // Parsear test cases (opcionales, una por línea)
    let testCasesArray: string[] = [];
    if (this.testCases().trim()) {
      testCasesArray = this.testCases()
        .split('\n')
        .map(t => t.trim())
        .filter(t => t.length > 0);
    }

    const exerciseData = {
      type: 'make_code',
      title: this.title().trim(),
      description: this.problemStatement().trim(),  // Backend: description = enunciado
      code: this.starterCode().trim() || undefined,  // Backend: code = código inicial
      solution: this.solutionCode().trim(),  // Backend: solution = código solución
      test_cases: testCasesArray.length > 0 ? testCasesArray : undefined,
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
