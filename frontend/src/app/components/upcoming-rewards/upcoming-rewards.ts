// frontend/src/app/components/upcoming-rewards/upcoming-rewards.ts

import { Component, Input, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { trigger, state, style, transition, animate } from '@angular/animations';

export interface UpcomingReward {
  _id: string;
  title: string;
  reward_type: string;
  points: number;
  progress?: {
    current: number;
    required: number;
    percentage: number;
  };
}

@Component({
  selector: 'app-upcoming-rewards',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './upcoming-rewards.html',
  styleUrl: './upcoming-rewards.css',
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class UpcomingRewardsComponent implements OnInit {
  // 📥 Input: Lista de recompensas próximas
  @Input() rewards: UpcomingReward[] = [];
  
  // 🔌 Estado local
  public isExpanded = signal(false);
  public currentRewardIndex = signal(0);

  ngOnInit(): void {
    console.log('📊 Recompensas próximas cargadas:', this.rewards);
  }

  /**
   * 🔄 Obtener recompensa actual
   */
  get currentReward(): UpcomingReward | undefined {
    return this.rewards[this.currentRewardIndex()];
  }

  /**
   * ➡️ Siguiente recompensa
   */
  nextReward(): void {
    if (this.currentRewardIndex() < this.rewards.length - 1) {
      this.currentRewardIndex.update(i => i + 1);
    }
  }

  /**
   * ⬅️ Recompensa anterior
   */
  previousReward(): void {
    if (this.currentRewardIndex() > 0) {
      this.currentRewardIndex.update(i => i - 1);
    }
  }

  /**
   * 🎯 Toggle expandir/contraer
   */
  toggleExpanded(): void {
    this.isExpanded.update(v => !v);
  }

  /**
   * 📊 Obtener clase de barra de progreso
   */
  getProgressBarClass(percentage: number): string {
    if (percentage >= 100) return 'completed';
    if (percentage >= 75) return 'high';
    if (percentage >= 50) return 'medium';
    if (percentage >= 25) return 'low';
    return 'minimal';
  }

  /**
   * 🏆 Obtener icono según tipo de recompensa
   */
  getRewardTypeIcon(rewardType: string): string {
    const icons: { [key: string]: string } = {
      'lesson_perfect': '🎯',
      'streak_milestone': '🔥',
      'xp_milestone': '⭐',
      'custom': '🏆'
    };
    return icons[rewardType] || '🎁';
  }

  /**
   * 📝 Obtener descripción según tipo
   */
  getRewardDescription(reward: UpcomingReward): string {
    if (!reward.progress) return '';

    switch (reward.reward_type) {
      case 'xp_milestone':
        const xpRemaining = reward.progress.required - reward.progress.current;
        return `Falta ${xpRemaining} XP (${reward.progress.percentage}%)`;
      
      case 'streak_milestone':
        const daysRemaining = reward.progress.required - reward.progress.current;
        return `Falta ${daysRemaining} ${daysRemaining === 1 ? 'día' : 'días'} (${reward.progress.percentage}%)`;
      
      case 'lesson_perfect':
        return reward.progress.percentage === 100 ? '✅ Completada' : '📝 Incompleta';
      
      default:
        return `${reward.progress.percentage}%`;
    }
  }

  /**
   * 🔄 TrackBy para lista
   */
  trackByRewardId(index: number, reward: UpcomingReward): string {
    return reward._id;
  }
}
