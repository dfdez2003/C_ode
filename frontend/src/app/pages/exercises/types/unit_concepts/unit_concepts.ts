// frontend/src/app/pages/exercises/types/unit_concepts/unit_concepts.component.ts

import { Component, Input, Output, EventEmitter, signal, computed, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UnitConceptsExerciseData } from '../../../../models/content';

interface DraggedPair {
  concept: string;
  definition: string;
  id: number;
}

@Component({
  selector: 'app-unit-concepts-exercise',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './unit_concepts.html',
  styleUrl: './unit_concepts.css',
})
export class UnitConceptsExerciseComponent implements OnInit, OnChanges {
  @Input({ required: true }) exerciseData!: UnitConceptsExerciseData;
  @Input({ required: true }) exerciseTitle!: string;
  @Input({ required: true }) exercisePoints!: number;
  @Input({ required: true }) sessionId!: string;
  @Input({ required: true }) moduleId!: string;
  @Input({ required: true }) lessonId!: string;
  @Input({ required: true }) exerciseUuid!: string;
  
  @Output() onComplete = new EventEmitter<any>();
  
  // Estado
  public matchedPairs = signal<DraggedPair[]>([]);
  public hasSubmitted = signal(false);
  public showFeedback = signal(false);
  public isContinueClicked = signal(false);  // 🆕 Previene múltiples clics en "Continuar"
  
  // Listas disponibles
  public availableConcepts = signal<string[]>([]);
  public availableDefinitions = signal<string[]>([]);
  
  // Selección actual
  public selectedConcept = signal<string | null>(null);
  public selectedDefinition = signal<string | null>(null);
  
  private correctPairs: Map<string, string> = new Map();
  private nextPairId = 1;
  private previousConceptsJSON = '';
  
  ngOnInit() {
    this.initializeExercise();
    this.previousConceptsJSON = JSON.stringify(this.exerciseData.concepts);
  }
  
  ngOnChanges(changes: SimpleChanges): void {
    if (changes['exerciseData'] && !changes['exerciseData'].firstChange) {
      const currentJSON = JSON.stringify(this.exerciseData.concepts);
      if (currentJSON !== this.previousConceptsJSON) {
        this.previousConceptsJSON = currentJSON;
        this.initializeExercise();
      }
    }
  }
  
  private initializeExercise(): void {
    // Resetear estado
    this.matchedPairs.set([]);
    this.hasSubmitted.set(false);
    this.showFeedback.set(false);
    this.isContinueClicked.set(false);  // 🆕 Resetear flag de continuar
    this.selectedConcept.set(null);
    this.selectedDefinition.set(null);
    this.correctPairs.clear();
    this.nextPairId = 1;
    
    // Cargar nuevos datos
    const concepts = this.exerciseData?.concepts || {};
    Object.entries(concepts).forEach(([concept, definition]) => {
      this.correctPairs.set(concept, definition);
    });
    
    const conceptsList = Array.from(this.correctPairs.keys());
    const definitionsList = Array.from(this.correctPairs.values());
    
    this.availableConcepts.set(this.shuffle(conceptsList));
    this.availableDefinitions.set(this.shuffle(definitionsList));
  }
  
  private shuffle<T>(array: T[]): T[] {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }
  
  selectConcept(concept: string): void {
    if (this.hasSubmitted()) return;
    
    this.selectedConcept.set(concept);
    
    // Si ya hay una definición seleccionada, crear el par
    if (this.selectedDefinition()) {
      this.createPair();
    }
  }
  
  selectDefinition(definition: string): void {
    if (this.hasSubmitted()) return;
    
    this.selectedDefinition.set(definition);
    
    // Si ya hay un concepto seleccionado, crear el par
    if (this.selectedConcept()) {
      this.createPair();
    }
  }
  
  private createPair(): void {
    const concept = this.selectedConcept();
    const definition = this.selectedDefinition();
    
    if (concept && definition) {
      const newPair: DraggedPair = {
        concept,
        definition,
        id: this.nextPairId++
      };
      
      this.matchedPairs.update(pairs => [...pairs, newPair]);
      
      // Remover de las listas disponibles
      this.availableConcepts.update(concepts => 
        concepts.filter(c => c !== concept)
      );
      this.availableDefinitions.update(definitions => 
        definitions.filter(d => d !== definition)
      );
      
      // Limpiar selecciones
      this.selectedConcept.set(null);
      this.selectedDefinition.set(null);
    }
  }
  
  separatePair(pair: DraggedPair): void {
    if (this.hasSubmitted()) return;
    
    this.matchedPairs.update(pairs => pairs.filter(p => p.id !== pair.id));
    this.availableConcepts.update(concepts => [...concepts, pair.concept]);
    this.availableDefinitions.update(definitions => [...definitions, pair.definition]);
  }
  
  isPairCorrect(pair: DraggedPair): boolean | null {
    if (!this.hasSubmitted()) return null;
    return this.correctPairs.get(pair.concept) === pair.definition;
  }
  
  public allPairsMatched = computed(() => {
    return this.matchedPairs().length === this.correctPairs.size;
  });
  
  public allPairsCorrect = computed(() => {
    if (!this.hasSubmitted()) return false;
    return this.matchedPairs().every(pair => 
      this.correctPairs.get(pair.concept) === pair.definition
    );
  });
  
  public correctPairsCount = computed(() => {
    if (!this.hasSubmitted()) return 0;
    return this.matchedPairs().filter(pair => 
      this.correctPairs.get(pair.concept) === pair.definition
    ).length;
  });
  
  checkAnswer(): void {
    if (!this.allPairsMatched() || this.hasSubmitted()) return;
    
    this.hasSubmitted.set(true);
    this.showFeedback.set(true);
  }
  
  /**
   * Continuar al siguiente ejercicio
   */
  continue(): void {
    if (!this.hasSubmitted()) return;
    
    // Prevenir múltiples clics
    if (this.isContinueClicked()) {
      console.log('⚠️ Botón Continuar ya fue presionado');
      return;
    }
    
    this.isContinueClicked.set(true);
    
    // Preparar datos de respuesta
    const pairs = this.matchedPairs().map(pair => ({
      concept: pair.concept,
      definition: pair.definition
    }));
    
    // Emitir con los pares
    this.onComplete.emit({ pairs });
  }
}
