// frontend/src/app/pages/game-map/components/module-edit-modal/module-edit-modal.ts
import { Component, signal, input, output, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-module-edit-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './module-edit-modal.html',
  styleUrl: './module-edit-modal.css',
})
export class ModuleEditModal {
  // Inputs
  moduleToEdit = input<any | null>(null);

  // Outputs
  close = output<void>();
  save = output<any>();

  // Signals para el formulario
  public title = signal('');
  public description = signal('');
  public order = signal(0);
  public estimateTime = signal(30);

  constructor() {
    // Effect para cargar datos cuando se recibe un módulo
    effect(() => {
      const module = this.moduleToEdit();
      if (module) {
        this.title.set(module.title || '');
        this.description.set(module.description || '');
        this.order.set(module.order || 0);
        this.estimateTime.set(module.estimate_time || 30);
      } else {
        this.resetForm();
      }
    });
  }

  onSubmit(): void {
    // Validaciones básicas
    if (!this.title().trim()) {
      alert('⚠️ El título es obligatorio');
      return;
    }

    if (this.title().trim().length < 3) {
      alert('⚠️ El título debe tener al menos 3 caracteres');
      return;
    }

    if (!this.description().trim()) {
      alert('⚠️ La descripción es obligatoria');
      return;
    }

    if (this.description().trim().length < 10) {
      alert('⚠️ La descripción debe tener al menos 10 caracteres');
      return;
    }

    if (this.order() < 0) {
      alert('⚠️ El orden no puede ser negativo');
      return;
    }

    if (this.estimateTime() < 1 || this.estimateTime() > 500) {
      alert('⚠️ El tiempo estimado debe estar entre 1 y 500 minutos');
      return;
    }

    const updatedModule = {
      title: this.title().trim(),
      description: this.description().trim(),
      order: this.order(),
      estimate_time: this.estimateTime()
    };

    this.save.emit(updatedModule);
  }

  onCancel(): void {
    this.close.emit();
  }

  private resetForm(): void {
    this.title.set('');
    this.description.set('');
    this.order.set(0);
    this.estimateTime.set(30);
  }

  onBackdropClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-backdrop')) {
      this.onCancel();
    }
  }
}
