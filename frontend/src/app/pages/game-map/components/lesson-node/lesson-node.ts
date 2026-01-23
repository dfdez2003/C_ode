// frontend/src/app/pages/game-map/components/lesson-node/lesson-node.ts

import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LessonOut } from '../../../../models/content';

@Component({
  selector: 'app-lesson-node',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './lesson-node.html',
  styleUrl: './lesson-node.css',
})
export class LessonNodeComponent {
  @Input({ required: true }) lesson!: LessonOut;
  @Input() lessonIndex: number = 0;
  @Input() isTeacher: boolean = false;

  /**
   * Determina el estado visual de la lección
   * TODO: Integrar con el estado real del progreso del usuario
   */
  getLessonStatus(): 'completed' | 'available' | 'locked' {
    // Por ahora, todas las lecciones están disponibles
    // Después integraremos con el servicio de progreso
    return 'available';
  }

  /**
   * Obtiene el icono según el estado
   */
  getStatusIcon(): string {
    const status = this.getLessonStatus();
    switch (status) {
      case 'completed':
        return '✅';
      case 'locked':
        return '🔒';
      default:
        return this.lesson.is_private ? '🔴' : '🔵';
    }
  }

  /**
   * Obtiene la clase CSS según el estado
   */
  getStatusClass(): string {
    return this.getLessonStatus();
  }
}
