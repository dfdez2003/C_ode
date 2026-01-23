// frontend/src/app/pages/exercises/types/make-code/make-code.ts

import { Component, Input, Output, EventEmitter, signal, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MakeCodeExerciseData } from '../../../../models/content';

@Component({
  selector: 'app-make-code',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './make-code.html',
  styleUrl: './make-code.css',
})
export class MakeCodeExerciseComponent implements OnInit, OnChanges {
  @Input({ required: true }) exerciseData!: MakeCodeExerciseData;
  @Input({ required: true }) exerciseTitle!: string;
  @Input({ required: true }) exercisePoints!: number;
  @Input({ required: true }) sessionId!: string;
  @Input({ required: true }) moduleId!: string;
  @Input({ required: true }) lessonId!: string;
  @Input({ required: true }) exerciseUuid!: string;
  
  // ✅ Recibir resultado del backend
  @Input() submissionResult: any = null;
  
  @Output() onComplete = new EventEmitter<any>();
  @Output() onContinue = new EventEmitter<void>();  // ✅ NUEVO: Para el botón continuar
  
  // Estado del componente
  public userCode = signal<string>('');
  public hasSubmitted = signal(false);
  public isSubmitting = signal(false);
  public isContinueClicked = signal(false);
  
  // Guardar el código enviado para emitirlo en continue
  private submittedCode: string = '';
  
  // ✅ Computed: Obtener feedback del backend
  public get codeFeedback(): any {
    return this.submissionResult?.code_feedback || null;
  }
  
  public get isCorrect(): boolean {
    return this.submissionResult?.is_correct || false;
  }
  
  public get hasTests(): boolean {
    return this.exerciseData.test_cases && this.exerciseData.test_cases.length > 0;
  }
  
  private previousExerciseJSON = '';
  
  ngOnInit() {
    this.initializeExercise();
  }
  
  ngOnChanges(changes: SimpleChanges) {
    if (changes['exerciseData'] && !changes['exerciseData'].firstChange) {
      const currentExerciseJSON = JSON.stringify(this.exerciseData);
      if (currentExerciseJSON !== this.previousExerciseJSON) {
        console.log('🔄 Ejercicio cambió, reiniciando estado');
        this.initializeExercise();
      }
    }
    
    // ✅ Cuando llegue el resultado del backend, actualizar isSubmitting
    if (changes['submissionResult'] && this.submissionResult && this.isSubmitting()) {
      this.isSubmitting.set(false);
    }
  }
  
  initializeExercise(): void {
    this.previousExerciseJSON = JSON.stringify(this.exerciseData);
    this.userCode.set(this.exerciseData.code || '');
    this.hasSubmitted.set(false);
    this.isSubmitting.set(false);
    this.isContinueClicked.set(false);
    this.submittedCode = '';
  }
  
  /**
   * ✅ PASO 1: Enviar código al backend para validar
   * NO avanza al siguiente ejercicio, solo valida
   */
  submitCode(): void {
    if (this.isSubmitting()) return;
    
    this.isSubmitting.set(true);
    this.hasSubmitted.set(true);
    this.submittedCode = this.userCode();
    
    // ✅ Emitir código para que el padre lo envíe al backend
    this.onComplete.emit(this.submittedCode);
  }
  
  /**
   * ✅ PASO 2: Continuar al siguiente ejercicio (después de ver resultado)
   * Este botón es el que avanza, no submitCode()
   */
  continue(): void {
    if (this.isContinueClicked()) return;
    
    this.isContinueClicked.set(true);
    // ✅ Emitir evento para que el padre avance al siguiente ejercicio
    this.onContinue.emit();
  }
  
  /**
   * Inserta un tab (4 espacios) en el editor
   */
  handleTab(event: KeyboardEvent, textarea: HTMLTextAreaElement): void {
    if (event.key === 'Tab') {
      event.preventDefault();
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const currentCode = this.userCode();
      
      // Insertar 4 espacios
      const newCode = currentCode.substring(0, start) + '    ' + currentCode.substring(end);
      this.userCode.set(newCode);
      
      // Restaurar posición del cursor
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 4;
      }, 0);
    }
  }
}
