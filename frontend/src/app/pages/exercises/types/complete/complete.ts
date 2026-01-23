// frontend/src/app/pages/exercises/types/complete/complete.component.ts

import { Component, Input, Output, EventEmitter, signal, computed, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CompleteExerciseData } from '../../../../models/content';

@Component({
  selector: 'app-complete-exercise',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './complete.html',
  styleUrl: './complete.css',
})
export class CompleteExerciseComponent implements OnInit, OnChanges {
  // Recibe los datos del ejercicio - Convertido a signal
  private _exerciseData = signal<CompleteExerciseData | undefined>(undefined);
  private _isFirstSet = true;
  
  @Input({ required: true })
  set exerciseData(value: CompleteExerciseData) {
    const newJSON = JSON.stringify(value);
    
    if (!this._isFirstSet && newJSON !== this.previousExerciseJSON) {
      this.previousExerciseJSON = newJSON;
      this._exerciseData.set(value);
      this.initializeExercise();
    } else {
      this._exerciseData.set(value);
      if (this._isFirstSet) {
        this.previousExerciseJSON = newJSON;
        this._isFirstSet = false;
      }
    }
  }
  get exerciseData(): CompleteExerciseData {
    return this._exerciseData()!;
  }
  
  @Input({ required: true }) exerciseTitle!: string;
  @Input({ required: true }) exercisePoints!: number;
  @Input({ required: true }) sessionId!: string;
  @Input({ required: true }) moduleId!: string;
  @Input({ required: true }) lessonId!: string;
  @Input({ required: true }) exerciseUuid!: string;
  
  // Emite cuando el usuario completa el ejercicio correctamente
  @Output() onComplete = new EventEmitter<any>();
  
  // Estado del componente
  public selectedAnswer = signal<string | null>(null);
  public hasSubmitted = signal(false);
  public showFeedback = signal(false);
  
  // Para detectar cambios
  private previousExerciseJSON = '';
  
  // ¿La respuesta es correcta?
  public isCorrect = computed(() => {
    if (!this.hasSubmitted()) return null;
    const data = this._exerciseData();
    return data ? this.selectedAnswer() === data.correct_answer : null;
  });
  
  // Texto formateado con la respuesta seleccionada
  public displayText = computed(() => {
    const data = this._exerciseData();
    if (!data) return '';
    
    const text = data.text;
    const answer = this.selectedAnswer();
    
    if (answer) {
      // Reemplazar ___ con la respuesta seleccionada
      return text.replace('___', `<strong class="answer-highlight">${answer}</strong>`);
    }
    
    return text;
  });

  ngOnInit(): void {
    this.initializeExercise();
    this.previousExerciseJSON = JSON.stringify(this.exerciseData);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['exerciseData'] && !changes['exerciseData'].firstChange) {
      const currentJSON = JSON.stringify(this.exerciseData);
      if (currentJSON !== this.previousExerciseJSON) {
        this.previousExerciseJSON = currentJSON;
        this.initializeExercise();
      }
    }
  }

  private initializeExercise(): void {
    this.selectedAnswer.set(null);
    this.hasSubmitted.set(false);
    this.showFeedback.set(false);
  }
  
  /**
   * Selecciona una opción de respuesta
   */
  selectAnswer(option: string): void {
    if (!this.hasSubmitted()) {
      this.selectedAnswer.set(option);
    }
  }
  
  /**
   * Verifica la respuesta seleccionada
   */
  checkAnswer(): void {
    const selected = this.selectedAnswer();
    if (selected && !this.hasSubmitted()) {
      // Mostrar feedback local
      this.hasSubmitted.set(true);
      this.showFeedback.set(true);
    }
  }

  /**
   * Continúa al siguiente ejercicio
   */
  continueToNext(): void {
    // ✅ Emitir con los datos de respuesta
    this.onComplete.emit({ answer: this.selectedAnswer() });
  }
}
