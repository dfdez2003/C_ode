// frontend/src/app/pages/lesson-editor/components/study-exercise-form/study-exercise-form.ts

import { Component, inject, signal, input, output, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface Flashcard {
  front: string;
  back: string;
}

@Component({
  selector: 'app-study-exercise-form',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './study-exercise-form.html',
  styleUrl: './study-exercise-form.css',
})
export class StudyExerciseFormComponent implements OnInit {
  
  // ========== INPUTS ==========
  
  public exercise = input<any | null>(null); // Si existe, es edición
  
  // ========== OUTPUTS ==========
  
  public close = output<void>();
  public save = output<any>();

  // ========== SIGNALS ==========
  
  public title = signal('');
  public xpReward = signal(15);
  public flashcards = signal<Flashcard[]>([
    { front: '', back: '' }
  ]);
  public isSubmitting = signal(false);
  public error = signal<string | null>(null);

  // ========== LIFECYCLE ==========

  ngOnInit(): void {
    const ex = this.exercise();
    if (ex) {
      // Modo edición: cargar datos
      this.title.set(ex.title || '');
      this.xpReward.set(ex.xp_reward || ex.points || 15);
      
      // Convertir flashcards de objeto a array
      if (ex.flashcards) {
        if (Array.isArray(ex.flashcards)) {
          // Ya es array
          this.flashcards.set([...ex.flashcards]);
        } else if (typeof ex.flashcards === 'object') {
          // Convertir objeto a array
          const flashcardsArray = Object.entries(ex.flashcards).map(([front, back]) => ({
            front,
            back: back as string
          }));
          this.flashcards.set(flashcardsArray);
          console.log('📚 Flashcards convertidas:', flashcardsArray);
        }
      }
    }
  }

  // ========== COMPUTED ==========

  public get isEditing(): boolean {
    return !!this.exercise();
  }

  public get modalTitle(): string {
    return this.isEditing ? '✏️ Editar Estudio (Flashcards)' : '➕ Crear Estudio (Flashcards)';
  }

  // ========== MÉTODOS DE FLASHCARDS ==========

  /**
   * Agregar nueva flashcard vacía
   */
  public addFlashcard(): void {
    this.flashcards.update(cards => [...cards, { front: '', back: '' }]);
  }

  /**
   * Eliminar flashcard por índice
   */
  public removeFlashcard(index: number): void {
    if (this.flashcards().length <= 1) {
      this.error.set('Debe haber al menos 1 flashcard');
      return;
    }
    
    this.flashcards.update(cards => cards.filter((_, i) => i !== index));
  }

  /**
   * Actualizar el frente de una flashcard
   */
  public updateFront(index: number, value: string): void {
    this.flashcards.update(cards => {
      const updated = [...cards];
      updated[index] = { ...updated[index], front: value };
      return updated;
    });
  }

  /**
   * Actualizar el reverso de una flashcard
   */
  public updateBack(index: number, value: string): void {
    this.flashcards.update(cards => {
      const updated = [...cards];
      updated[index] = { ...updated[index], back: value };
      return updated;
    });
  }

  /**
   * Mover flashcard hacia arriba
   */
  public moveUp(index: number): void {
    if (index === 0) return;
    
    this.flashcards.update(cards => {
      const updated = [...cards];
      [updated[index - 1], updated[index]] = [updated[index], updated[index - 1]];
      return updated;
    });
  }

  /**
   * Mover flashcard hacia abajo
   */
  public moveDown(index: number): void {
    if (index === this.flashcards().length - 1) return;
    
    this.flashcards.update(cards => {
      const updated = [...cards];
      [updated[index], updated[index + 1]] = [updated[index + 1], updated[index]];
      return updated;
    });
  }

  // ========== MÉTODOS DEL FORMULARIO ==========

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

    // Validaciones básicas
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

    // Validar flashcards
    const cards = this.flashcards();
    
    if (cards.length === 0) {
      this.error.set('Debe haber al menos 1 flashcard');
      return;
    }

    for (let i = 0; i < cards.length; i++) {
      if (!cards[i].front.trim()) {
        this.error.set(`Flashcard ${i + 1}: El frente no puede estar vacío`);
        return;
      }
      
      if (!cards[i].back.trim()) {
        this.error.set(`Flashcard ${i + 1}: El reverso no puede estar vacío`);
        return;
      }
    }

    // Crear objeto del ejercicio
    const exerciseData = {
      type: 'study',
      title: this.title().trim(),
      xp_reward: this.xpReward(),
      flashcards: cards.map(card => ({
        front: card.front.trim(),
        back: card.back.trim()
      }))
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
