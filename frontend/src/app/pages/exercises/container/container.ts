// frontend/src/app/pages/exercises/container/container.component.ts

import { Component, Input, OnInit, OnDestroy, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ExerciseSummary } from '../../../models/content';
import { ExerciseBaseComponent } from '../base/base';
import { SessionService } from '../../../services/session/session.service';
import { ProgressService, ProgressResponse } from '../../../services/progress/progress.service';
import { AuthService } from '../../../services/auth/auth';

@Component({
  selector: 'app-exercise-container',
  standalone: true,
  imports: [CommonModule, ExerciseBaseComponent], 
  templateUrl: './container.html',
  styleUrl: './container.css',
})
export class ContainerComponent implements OnInit, OnDestroy {
  // 🔌 Servicios inyectados
  private sessionService = inject(SessionService);
  private progressService = inject(ProgressService);
  private authService = inject(AuthService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  // Recibe la lista completa de ejercicios de la lección
  @Input({ required: true }) exercises!: ExerciseSummary[]; 
  @Input({ required: true }) lessonId!: string;
  @Input({ required: true }) moduleId!: string;
  
  // 🎯 Estado del contenedor
  public currentExerciseIndex = signal<number>(0);
  public sessionId = signal<string | null>(null);
  public isLessonCompleted = signal<boolean>(false);
  public showRewardModal = signal<boolean>(false);
  public rewardDetails = signal<ProgressResponse | null>(null);
  
  // 📊 Estadísticas de la lección
  public totalXPEarned = signal<number>(0);
  public exercisesCompleted = signal<number>(0);
  public correctAnswers = signal<number>(0);
  public currentScore = signal<number>(0);  // Puntos del intento actual
  public totalPossible = signal<number>(0); // Puntos totales posibles

  /**
   * 🚀 Inicialización del componente
   * Se ejecuta al cargar la lección - inicia una nueva sesión de estudio
   */
  async ngOnInit(): Promise<void> {
    console.log('📚 Iniciando lección...', this.lessonId);
    
    // Iniciar sesión de estudio
    try {
      const sessionId = await this.sessionService.startSession();
      this.sessionId.set(sessionId);
      console.log('✅ Sesión iniciada:', sessionId);
    } catch (error) {
      console.error('❌ Error al iniciar sesión:', error);
    }
  }

  /**
   * 🛑 Limpieza del componente
   * Finaliza la sesión cuando el usuario sale de la lección
   */
  async ngOnDestroy(): Promise<void> {
    console.log('👋 Saliendo de la lección...');
    
    // Finalizar sesión si está activa
    if (this.sessionService.hasActiveSession()) {
      await this.sessionService.endSession();
      console.log('✅ Sesión finalizada');
    }
  }

  /**
   * 📊 Obtiene el ejercicio actual basado en el índice.
   * Computed signal que reacciona a cambios en currentExerciseIndex
   */
  public currentExercise = computed(() => {
    const index = this.currentExerciseIndex();
    const exercise = this.exercises[index];
    console.log('🔵 Container - currentExercise computed, index:', index, 'exercise:', exercise);
    return exercise;
  });

  /**
   * ➡️ Navegar al siguiente ejercicio
   */
  public nextExercise(): void {
    const currentIndex = this.currentExerciseIndex();
    const lastResult = this.progressService.lastSubmissionResult();
    
    console.log('🔵 nextExercise() llamado');
    console.log('  📍 Index actual:', currentIndex);
    console.log('  📍 Total ejercicios:', this.exercises.length);
    console.log('  📊 lastResult:', lastResult);
    
    // Actualizar estadísticas de ejercicios (NO puntos todavía)
    if (lastResult) {
      console.log('📊 Actualizando estadísticas con:', lastResult);
      
      // Contar ejercicios completados
      this.exercisesCompleted.set(this.exercisesCompleted() + 1);
      
      // Contar respuestas correctas
      if (lastResult.is_correct) {
        this.correctAnswers.set(this.correctAnswers() + 1);
      }
      
      // Actualizar puntaje actual y total posible
      if (lastResult.current_score !== undefined) {
        this.currentScore.set(lastResult.current_score);
      }
      if (lastResult.total_possible !== undefined) {
        this.totalPossible.set(lastResult.total_possible);
      }
      
      console.log('📊 Estadísticas actualizadas:');
      console.log('  ✅ Correctas:', this.correctAnswers());
      console.log('  📝 Completados:', this.exercisesCompleted());
      console.log('  📊 Puntaje:', this.currentScore(), '/', this.totalPossible());
      
      // Si la lección terminó según el backend, finalizar
      if (lastResult.lesson_finished) {
        console.log('🎉 Backend indica lesson_finished = true');
        this.completeLessonAndFinishSession();
        return;
      }
    }
    
    // Si no terminó, avanzar al siguiente ejercicio
    if (currentIndex < this.exercises.length - 1) {
      const newIndex = currentIndex + 1;
      console.log(`🔵 Container - Avanzando de ejercicio ${currentIndex} → ${newIndex}`);
      console.log(`🔵 Ejercicio actual:`, this.exercises[currentIndex]);
      console.log(`🔵 Próximo ejercicio:`, this.exercises[newIndex]);
      this.currentExerciseIndex.set(newIndex);
      console.log(`➡️ Siguiente ejercicio (${newIndex + 1}/${this.exercises.length})`);
    } else {
      // Por seguridad, si llegamos al final sin lesson_finished, mostrar error
      console.error('❌ ERROR: Llegamos al último ejercicio pero lesson_finished no es true');
      console.error('❌ Esto no debería pasar. Verificar backend.');
    }
  }

  /**
   * 🎉 Completar la lección y finalizar la sesión
   */
  private async completeLessonAndFinishSession(): Promise<void> {
    console.log('🎉 ¡Lección completada!');
    
    // Obtener el resultado del último ejercicio (que contiene reward_details)
    const lastResult = this.progressService.lastSubmissionResult();
    console.log('📊 lastSubmissionResult completo:', JSON.stringify(lastResult, null, 2));
    
    // Extraer XP total de reward_details (calculado por el backend)
    if (lastResult && lastResult.reward_details) {
      const totalXP = lastResult.reward_details.total_xp_earned || 0;
      this.totalXPEarned.set(totalXP);
      this.rewardDetails.set(lastResult);
      
      console.log('💰 XP Total de la lección:', totalXP);
      console.log('🏆 Detalles de recompensa:', lastResult.reward_details);
    } else {
      // Si no hay reward_details, mantener en 0
      console.error('❌ ERROR: No se recibieron reward_details del backend');
      console.error('❌ lastResult:', lastResult);
      this.totalXPEarned.set(0);
    }
    
    console.log('📊 Estadísticas finales antes de mostrar:');
    console.log('  💰 Total XP:', this.totalXPEarned());
    console.log('  ✅ Correctas:', this.correctAnswers());
    console.log('  📝 Completados:', this.exercisesCompleted());
    
    // Marcar lección como completada (esto muestra la pantalla de estadísticas)
    this.isLessonCompleted.set(true);
    
    // Finalizar sesión
    await this.sessionService.endSession();
  }

  /**
   * ⬅️ Volver a la lista de lecciones del módulo
   */
  public goBackToLessons(): void {
    this.router.navigate(['/module', this.moduleId]);
  }

  /**
   * ⬅️ Navegar al ejercicio anterior (ELIMINADO - No se regresa)
   */
  /*
  public previousExercise(): void {
    const currentIndex = this.currentExerciseIndex();
    
    if (currentIndex > 0) {
      this.currentExerciseIndex.set(currentIndex - 1);
      console.log(`⬅️ Ejercicio anterior (${currentIndex}/${this.exercises.length})`);
    }
  }
  */

  /**
   * 📈 Obtener el progreso de la lección (porcentaje)
   */
  get lessonProgress(): number {
    const currentIndex = this.currentExerciseIndex();
    return Math.round(((currentIndex + 1) / this.exercises.length) * 100);
  }

  /**
   * ⏱️ Obtener la duración de la sesión formateada
   */
  get sessionDuration(): string {
    return this.sessionService.getFormattedDuration();
  }

  /**
   * 🗺️ Volver al mapa de aprendizaje (desde botón de completado)
   */
  public goBackToMap(): void {
    this.router.navigate(['/game-map']);
  }

  /**
   * 🚪 Salir de la lección (en medio de los ejercicios)
   */
  public exitLesson(): void {
    const confirmed = confirm('¿Seguro que quieres salir? Tu progreso se guardará automáticamente.');
    if (confirmed) {
      this.router.navigate(['/game-map']);
    }
  }
}
