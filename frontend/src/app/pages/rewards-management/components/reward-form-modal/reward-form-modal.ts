import { Component, EventEmitter, Input, Output, signal, effect, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ContentService } from '../../../../services/content/content';
import { LessonOut } from '../../../../models/content';

export interface RewardFormData {
  title: string;
  description: string;
  icon: string;
  reward_type: 'lesson_perfect' | 'streak_milestone' | 'xp_milestone' | 'custom';
  criteria?: any;
  xp_bonus: number;
  is_active: boolean;
}

@Component({
  selector: 'app-reward-form-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './reward-form-modal.html',
  styleUrls: ['./reward-form-modal.css']
})
export class RewardFormModalComponent {
  @Input() isEdit = false;
  @Input() reward: any = null;
  @Output() onSave = new EventEmitter<RewardFormData>();
  @Output() onCancel = new EventEmitter<void>();

  form!: FormGroup;
  contentService = inject(ContentService);
  
  // Signals para datos dinámicos
  lessons = signal<LessonOut[]>([]);
  selectedLessonId = signal<string>('');
  xpThreshold = signal<number>(100);
  streakDays = signal<number>(3);
  loadingLessons = signal(false);

  rewardTypes = [
    { value: 'lesson_perfect', label: 'Lección Perfecta' },
    { value: 'streak_milestone', label: 'Racha Alcanzada' },
    { value: 'xp_milestone', label: 'XP Alcanzado' },
    { value: 'custom', label: 'Personalizada' }
  ];

  commonIcons = ['🏆', '⭐', '🎖️', '🎁', '💎', '🔥', '⚡', '🌟', '🎯', '👑', '💪', '🚀'];

  constructor(private fb: FormBuilder) {
    this.initForm();
    this.loadLessonsData();

    effect(() => {
      if (this.reward) {
        this.loadRewardData();
      }
    });
  }

  initForm(): void {
    this.form = this.fb.group({
      title: ['', [Validators.required, Validators.minLength(1), Validators.maxLength(100)]],
      description: ['', [Validators.required, Validators.minLength(1), Validators.maxLength(500)]],
      icon: ['🎁', Validators.required],
      reward_type: ['lesson_perfect', Validators.required],
      xp_bonus: [100, [Validators.required, Validators.min(1)]],
      is_active: [true]
    });
  }

  loadLessonsData(): void {
    this.loadingLessons.set(true);
    this.contentService.getModules().subscribe({
      next: (modules) => {
        // Extraer todas las lecciones de todos los módulos
        const allLessons: LessonOut[] = [];
        modules.forEach(module => {
          if (module.lessons && Array.isArray(module.lessons)) {
            allLessons.push(...module.lessons);
          }
        });
        this.lessons.set(allLessons);
        this.loadingLessons.set(false);
      },
      error: (err) => {
        console.error('Error cargando lecciones:', err);
        this.loadingLessons.set(false);
      }
    });
  }

  loadRewardData(): void {
    if (this.reward) {
      this.form.patchValue({
        title: this.reward.title,
        description: this.reward.description,
        icon: this.reward.icon,
        reward_type: this.reward.reward_type,
        xp_bonus: this.reward.xp_bonus,
        is_active: this.reward.is_active
      });

      // Cargar criterios específicos según el tipo
      if (this.reward.criteria) {
        const type = this.reward.reward_type;
        
        if (type === 'lesson_perfect' && this.reward.criteria.lesson_id) {
          this.selectedLessonId.set(this.reward.criteria.lesson_id);
        } else if (type === 'xp_milestone' && this.reward.criteria.xp_threshold) {
          this.xpThreshold.set(this.reward.criteria.xp_threshold);
        } else if (type === 'streak_milestone' && this.reward.criteria.streak) {
          this.streakDays.set(this.reward.criteria.streak);
        }
      }
    }
  }

  selectIcon(icon: string): void {
    this.form.patchValue({ icon });
  }

  onRewardTypeChange(): void {
    // Reiniciar valores de criterios cuando cambia el tipo
    this.selectedLessonId.set('');
    this.xpThreshold.set(100);
    this.streakDays.set(3);
  }

  onSubmit(): void {
    if (this.form.invalid) {
      Object.keys(this.form.controls).forEach(key => {
        const control = this.form.get(key);
        if (control?.invalid) {
          control.markAsTouched();
        }
      });
      return;
    }

    const rewardType = this.form.get('reward_type')?.value;
    let criteria: any = undefined;

    // Construir criterios según el tipo seleccionado
    switch (rewardType) {
      case 'lesson_perfect':
        if (!this.selectedLessonId()) {
          alert('Por favor selecciona una lección');
          return;
        }
        criteria = { lesson_id: this.selectedLessonId() };
        break;

      case 'xp_milestone':
        if (this.xpThreshold() <= 0) {
          alert('Por favor ingresa un valor de XP válido');
          return;
        }
        criteria = { xp_threshold: this.xpThreshold() };
        break;

      case 'streak_milestone':
        if (this.streakDays() <= 0) {
          alert('Por favor ingresa un número de días válido');
          return;
        }
        criteria = { streak: this.streakDays() };
        break;

      case 'custom':
        // Para custom no se requieren criterios específicos
        criteria = {};
        break;
    }

    const formData: RewardFormData = {
      ...this.form.value,
      criteria
    };

    this.onSave.emit(formData);
  }

  cancel(): void {
    this.onCancel.emit();
  }

  // Helper methods for template
  hasError(field: string, error: string): boolean {
    const control = this.form.get(field);
    return !!(control && control.touched && control.hasError(error));
  }

  getErrorMessage(field: string): string {
    const control = this.form.get(field);
    if (!control || !control.touched) return '';

    if (control.hasError('required')) return 'Este campo es obligatorio';
    if (control.hasError('minlength')) {
      const min = control.errors?.['minlength'].requiredLength;
      return `Mínimo ${min} caracteres`;
    }
    if (control.hasError('maxlength')) {
      const max = control.errors?.['maxlength'].requiredLength;
      return `Máximo ${max} caracteres`;
    }
    if (control.hasError('min')) {
      const min = control.errors?.['min'].min;
      return `Debe ser mayor o igual a ${min}`;
    }

    return '';
  }
}
