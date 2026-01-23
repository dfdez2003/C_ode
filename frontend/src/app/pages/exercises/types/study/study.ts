// frontend/src/app/pages/exercises/types/study/study.component.ts

import { Component, Input, Output, EventEmitter, signal, computed, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StudyExerciseData } from '../../../../models/content';

@Component({
  selector: 'app-study-exercise',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './study.html',
  styleUrl: './study.css'
})
export class StudyExerciseComponent implements OnInit, OnChanges {
  // Recibe los datos del ejercicio (flashcards) - Convertido a signal
  private _exerciseData = signal<StudyExerciseData | undefined>(undefined);
  private _isFirstSet = true;
  
  @Input({ required: true }) 
  set exerciseData(value: StudyExerciseData) {
    console.log('🔷 Study - Nuevo exerciseData recibido via setter');
    const newJSON = JSON.stringify(value.flashcards);
    
    // Si no es el primer set y los datos cambiaron, reinicializar
    if (!this._isFirstSet && newJSON !== this.previousFlashcardsJSON) {
      console.log('🔷 Study - Flashcards cambiaron, reinicializando...');
      this.previousFlashcardsJSON = newJSON;
      this._exerciseData.set(value);
      this.initializeExercise();
    } else {
      console.log('🔷 Study - Primer set o flashcards iguales, solo actualizando signal');
      this._exerciseData.set(value);
      if (this._isFirstSet) {
        this.previousFlashcardsJSON = newJSON;
        this._isFirstSet = false;
      }
    }
  }
  get exerciseData(): StudyExerciseData {
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
  public currentCardIndex = signal(0);
  public isFlipped = signal(false);
  public cardsViewed = signal<Set<number>>(new Set());
  
  // Para detectar cambios
  private previousFlashcardsJSON = '';
  
  // Convertir el objeto flashcards a un array para iterar
  public flashcardsArray = computed(() => {
    const data = this._exerciseData();
    if (!data) return [];
    
    const flashcards = data.flashcards || {};
    const array = Object.entries(flashcards).map(([concept, definition]) => ({
      concept,
      definition
    }));
    console.log('🔷 Study - flashcardsArray computed:', array.length, 'cards');
    console.log('🔷 Flashcards completas:', flashcards);
    return array;
  });
  
  // Card actual
  public currentCard = computed(() => {
    const cards = this.flashcardsArray();
    const index = this.currentCardIndex();
    return cards[index];
  });
  
  // Progreso
  public progress = computed(() => {
    const total = this.flashcardsArray().length;
    const viewed = this.cardsViewed().size;
    return total > 0 ? Math.round((viewed / total) * 100) : 0;
  });

  ngOnInit(): void {
    console.log('🔷 Study ngOnInit - Inicializando');
    this.initializeExercise();
  }

  ngOnChanges(changes: SimpleChanges): void {
    // El setter ya maneja los cambios, este hook ya no es necesario
    // pero lo dejamos por compatibilidad
    console.log('🔷 Study ngOnChanges ejecutado (setter ya manejó el cambio)');
  }

  private initializeExercise(): void {
    console.log('🔄 Reinicializando ejercicio Study');
    this.currentCardIndex.set(0);
    this.isFlipped.set(false);
    this.cardsViewed.set(new Set());
  }
  
  // ¿Es la última card?
  public isLastCard = computed(() => {
    return this.currentCardIndex() === this.flashcardsArray().length - 1;
  });
  
  // ¿Todas las cards han sido vistas?
  public allCardsViewed = computed(() => {
    return this.cardsViewed().size === this.flashcardsArray().length;
  });
  
  /**
   * Voltea la card actual para mostrar la definición
   */
  flipCard(): void {
    this.isFlipped.set(!this.isFlipped());
    
    // Marcar como vista cuando se voltea
    if (this.isFlipped()) {
      const newViewed = new Set(this.cardsViewed());
      newViewed.add(this.currentCardIndex());
      this.cardsViewed.set(newViewed);
    }
  }
  
  /**
   * Navega a la siguiente card
   */
  nextCard(): void {
    const currentIndex = this.currentCardIndex();
    const maxIndex = this.flashcardsArray().length - 1;
    
    if (currentIndex < maxIndex) {
      this.currentCardIndex.set(currentIndex + 1);
      this.isFlipped.set(false);
    }
  }
  
  /**
   * Navega a la card anterior
   */
  previousCard(): void {
    const currentIndex = this.currentCardIndex();
    
    if (currentIndex > 0) {
      this.currentCardIndex.set(currentIndex - 1);
      this.isFlipped.set(false);
    }
  }
  
  /**
   * Completa el ejercicio
   * Solo se puede completar si todas las cards han sido vistas
   */
  completeExercise(): void {
    if (this.allCardsViewed()) {
      // Verificar que haya sessionId antes de emitir
      if (!this.sessionId) {
        console.warn('⚠️ Esperando a que la sesión esté activa...');
        return;
      }
      
      // ✅ Emitir con los datos de respuesta
      this.onComplete.emit({ viewed: true });
    }
  }
}