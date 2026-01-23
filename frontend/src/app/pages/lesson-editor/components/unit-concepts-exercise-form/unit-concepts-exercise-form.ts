// frontend/src/app/pages/lesson-editor/components/unit-concepts-exercise-form/unit-concepts-exercise-form.ts

import { Component, inject, signal, input, output, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface ConceptPair {
  concept: string;
  definition: string;
}

@Component({
  selector: 'app-unit-concepts-exercise-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './unit-concepts-exercise-form.html',
  styleUrl: './unit-concepts-exercise-form.css',
})
export class UnitConceptsExerciseFormComponent implements OnInit {
  
  // ========== INPUTS ==========
  
  public exercise = input<any | null>(null);
  
  // ========== OUTPUTS ==========
  
  public close = output<void>();
  public save = output<any>();

  // ========== SIGNALS ==========
  
  public title = signal('');
  public xpReward = signal(20);
  public pairs = signal<ConceptPair[]>([
    { concept: '', definition: '' },
    { concept: '', definition: '' }
  ]);
  public isSubmitting = signal(false);
  public error = signal<string | null>(null);

  // ========== LIFECYCLE ==========

  ngOnInit(): void {
    const ex = this.exercise();
    if (ex) {
      this.title.set(ex.title || '');
      this.xpReward.set(ex.xp_reward || ex.points || 20);
      
      // Convertir concepts de objeto a array de pares
      if (ex.concepts) {
        if (Array.isArray(ex.concepts)) {
          // Ya es array (no debería pasar)
          this.pairs.set([...ex.concepts]);
        } else if (typeof ex.concepts === 'object') {
          // Convertir objeto a array de pares
          const pairsArray = Object.entries(ex.concepts).map(([concept, definition]) => ({
            concept,
            definition: definition as string
          }));
          this.pairs.set(pairsArray);
          console.log('🔗 Conceptos convertidos:', pairsArray);
        }
      } else if (ex.pairs && Array.isArray(ex.pairs)) {
        // Por si acaso viene como "pairs"
        this.pairs.set([...ex.pairs]);
      }
    }
  }

  // ========== COMPUTED ==========

  public get isEditing(): boolean {
    return !!this.exercise();
  }

  public get modalTitle(): string {
    return this.isEditing ? '✏️ Editar Relacionar Conceptos' : '➕ Crear Relacionar Conceptos';
  }

  // ========== MÉTODOS DE PARES ==========

  public addPair(): void {
    this.pairs.update(pairs => [...pairs, { concept: '', definition: '' }]);
  }

  public removePair(index: number): void {
    if (this.pairs().length <= 2) {
      this.error.set('Debe haber al menos 2 pares de conceptos');
      return;
    }
    
    this.pairs.update(pairs => pairs.filter((_, i) => i !== index));
  }

  public updateConcept(index: number, value: string): void {
    this.pairs.update(pairs => {
      const updated = [...pairs];
      updated[index] = { ...updated[index], concept: value };
      return updated;
    });
  }

  public updateDefinition(index: number, value: string): void {
    this.pairs.update(pairs => {
      const updated = [...pairs];
      updated[index] = { ...updated[index], definition: value };
      return updated;
    });
  }

  public moveUp(index: number): void {
    if (index === 0) return;
    
    this.pairs.update(pairs => {
      const updated = [...pairs];
      [updated[index - 1], updated[index]] = [updated[index], updated[index - 1]];
      return updated;
    });
  }

  public moveDown(index: number): void {
    if (index === this.pairs().length - 1) return;
    
    this.pairs.update(pairs => {
      const updated = [...pairs];
      [updated[index], updated[index + 1]] = [updated[index + 1], updated[index]];
      return updated;
    });
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

    if (this.xpReward() < 5 || this.xpReward() > 100) {
      this.error.set('El XP debe estar entre 5 y 100');
      return;
    }

    const pairs = this.pairs();
    
    if (pairs.length < 2) {
      this.error.set('Debe haber al menos 2 pares de conceptos');
      return;
    }

    for (let i = 0; i < pairs.length; i++) {
      if (!pairs[i].concept.trim()) {
        this.error.set(`Par ${i + 1}: El concepto no puede estar vacío`);
        return;
      }
      
      if (!pairs[i].definition.trim()) {
        this.error.set(`Par ${i + 1}: La definición no puede estar vacía`);
        return;
      }
    }

    const exerciseData = {
      type: 'unit_concepts',
      title: this.title().trim(),
      xp_reward: this.xpReward(),
      pairs: pairs.map(pair => ({
        concept: pair.concept.trim(),
        definition: pair.definition.trim()
      }))
    };

    this.save.emit(exerciseData);
  }

  public onBackdropClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-backdrop')) {
      this.onCancel();
    }
  }
}
