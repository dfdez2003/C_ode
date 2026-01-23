// frontend/src/app/pages/game-map/components/module-node/module-node.ts

import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ModuleOut } from '../../../../models/content';
import { LessonNodeComponent } from '../lesson-node/lesson-node';

@Component({
  selector: 'app-module-node',
  standalone: true,
  imports: [CommonModule, LessonNodeComponent],
  templateUrl: './module-node.html',
  styleUrl: './module-node.css',
})
export class ModuleNodeComponent {
  @Input({ required: true }) module!: ModuleOut;
  @Input() isTeacher: boolean = false;

  // Eventos
  @Output() lessonClick = new EventEmitter<{ lessonId: string; lessonIndex: number }>();
  @Output() addLesson = new EventEmitter<void>();
  @Output() editModule = new EventEmitter<void>();
  @Output() deleteModule = new EventEmitter<void>();

  /**
   * Handler cuando se hace click en una lección
   */
  onLessonClick(lessonId: string, lessonIndex: number): void {
    this.lessonClick.emit({ lessonId, lessonIndex });
  }
}
