// frontend/src/app/pages/exercises/types/question/question.component.ts

import { Component, Input, Output, EventEmitter, signal, computed, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { QuestionExerciseData } from '../../../../models/content';

@Component({
  selector: 'app-question-exercise',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './question.html',
  styleUrl: './question.css',
})
export class QuestionExerciseComponent implements OnInit, OnChanges {
  // Recibe los datos del ejercicio - Convertido a signal
  private _exerciseData = signal<QuestionExerciseData | undefined>(undefined);
  private _isFirstSet = true;
  
  @Input({ required: true })
  set exerciseData(value: QuestionExerciseData) {
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
  get exerciseData(): QuestionExerciseData {
    return this._exerciseData()!;
  }
  
  @Input({ required: true }) exerciseTitle!: string;
  @Input({ required: true }) exercisePoints!: number;
  @Input({ required: true }) sessionId!: string;
  @Input({ required: true }) moduleId!: string;
  @Input({ required: true }) lessonId!: string;
  @Input({ required: true }) exerciseUuid!: string;
  
  // Emite cuando el usuario completa el ejercicio
  @Output() onComplete = new EventEmitter<any>();
  
  // Estado del componente
  public selectedOption = signal<string | null>(null);
  public hasSubmitted = signal(false);
  public showFeedback = signal(false);
  
  // Para detectar cambios
  private previousExerciseJSON = '';
  
  // Helper para obtener letra de opción (A, B, C, D...)
  getOptionLabel(index: number): string {
    return String.fromCharCode(65 + index);
  }
  
  // ¿La respuesta es correcta?
  public isCorrect = computed(() => {
    if (!this.hasSubmitted()) return null;
    const data = this._exerciseData();
    return data ? this.selectedOption() === data.correct_answer : null;
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
    this.selectedOption.set(null);
    this.hasSubmitted.set(false);
    this.showFeedback.set(false);
  }
  
  /**
   * Selecciona una opción de respuesta
   */
  selectOption(option: string): void {
    if (!this.hasSubmitted()) {
      this.selectedOption.set(option);
    }
  }
  
  /**
   * Verifica la respuesta seleccionada
   */
  checkAnswer(): void {
    const selected = this.selectedOption();
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
    this.onComplete.emit({ answer: this.selectedOption() });
  }
}
