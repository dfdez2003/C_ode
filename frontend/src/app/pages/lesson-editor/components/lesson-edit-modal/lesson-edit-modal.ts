import { Component, input, output, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-lesson-edit-modal',
  imports: [CommonModule, FormsModule],
  templateUrl: './lesson-edit-modal.html',
  styleUrl: './lesson-edit-modal.css',
})
export class LessonEditModal {
  // Input: Datos de la lección a editar
  lessonToEdit = input<any | null>(null);
  
  // Outputs
  close = output<void>();
  save = output<any>();

  // Señales para los campos del formulario
  public title = signal('');
  public description = signal('');
  public xpReward = signal(100);
  public isPrivate = signal(false);
  public order = signal(1);

  constructor() {
    // Efecto: Cargar datos cuando lessonToEdit cambia
    effect(() => {
      const lesson = this.lessonToEdit();
      if (lesson) {
        console.log('📖 Cargando datos de lección para editar:', lesson);
        this.title.set(lesson.title || '');
        this.description.set(lesson.description || '');
        this.xpReward.set(lesson.xp_reward || 100);
        this.isPrivate.set(lesson.is_private || false);
        this.order.set(lesson.order || 1);
      } else {
        // Reset si no hay lección
        this.resetForm();
      }
    });
  }

  resetForm(): void {
    this.title.set('');
    this.description.set('');
    this.xpReward.set(100);
    this.isPrivate.set(false);
    this.order.set(1);
  }

  onClose(): void {
    this.close.emit();
  }

  onSubmit(): void {
    // Validación básica
    if (!this.title().trim()) {
      alert('⚠️ El título es obligatorio');
      return;
    }

    if (this.xpReward() < 0) {
      alert('⚠️ La recompensa de XP no puede ser negativa');
      return;
    }

    if (this.order() < 1) {
      alert('⚠️ El orden debe ser al menos 1');
      return;
    }

    // Preparar datos actualizados
    const updatedLesson = {
      title: this.title().trim(),
      description: this.description().trim(),
      xp_reward: this.xpReward(),
      is_private: this.isPrivate(),
      order: this.order()
    };

    console.log('💾 Guardando lección actualizada:', updatedLesson);
    this.save.emit(updatedLesson);
  }
}
