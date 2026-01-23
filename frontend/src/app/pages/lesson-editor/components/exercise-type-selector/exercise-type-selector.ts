// frontend/src/app/pages/lesson-editor/components/exercise-type-selector/exercise-type-selector.ts

import { Component, output } from '@angular/core';
import { CommonModule } from '@angular/common';

export type ExerciseType = 'study' | 'complete' | 'make_code' | 'question' | 'unit_concepts';

interface ExerciseTypeOption {
  type: ExerciseType;
  icon: string;
  name: string;
  description: string;
  color: string;
}

@Component({
  selector: 'app-exercise-type-selector',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './exercise-type-selector.html',
  styleUrl: './exercise-type-selector.css',
})
export class ExerciseTypeSelectorComponent {
  
  // ========== OUTPUTS ==========
  
  public typeSelected = output<ExerciseType>();
  public close = output<void>();

  // ========== DATA ==========

  public exerciseTypes: ExerciseTypeOption[] = [
    {
      type: 'question',
      icon: '❓',
      name: 'Pregunta',
      description: 'Pregunta de opción múltiple o respuesta corta',
      color: '#3b82f6'
    },
    {
      type: 'study',
      icon: '📚',
      name: 'Estudio',
      description: 'Flashcards para memorizar conceptos',
      color: '#8b5cf6'
    },
    {
      type: 'complete',
      icon: '✏️',
      name: 'Completar Código',
      description: 'Ejercicio de completar espacios en código',
      color: '#10b981'
    },
    {
      type: 'make_code',
      icon: '💻',
      name: 'Escribir Código',
      description: 'Ejercicio de programación completo',
      color: '#f59e0b'
    },
    {
      type: 'unit_concepts',
      icon: '🧩',
      name: 'Conceptos',
      description: 'Relacionar conceptos con definiciones',
      color: '#ef4444'
    }
  ];

  // ========== MÉTODOS ==========

  /**
   * Seleccionar tipo de ejercicio
   */
  public onSelectType(type: ExerciseType): void {
    this.typeSelected.emit(type);
  }

  /**
   * Cerrar modal
   */
  public onClose(): void {
    this.close.emit();
  }

  /**
   * Cerrar al hacer click en backdrop
   */
  public onBackdropClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-backdrop')) {
      this.onClose();
    }
  }
}
