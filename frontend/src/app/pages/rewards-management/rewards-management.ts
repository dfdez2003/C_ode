// frontend/src/app/pages/rewards-management/rewards-management.ts

import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { RewardsService, Reward, RewardCreate, RewardUpdate } from '../../services/rewards/rewards.service';
import { RewardFormModalComponent } from './components/reward-form-modal';

@Component({
  selector: 'app-rewards-management',
  standalone: true,
  imports: [CommonModule, RewardFormModalComponent],
  templateUrl: './rewards-management.html',
  styleUrl: './rewards-management.css',
})
export class RewardsManagementComponent implements OnInit {
  private rewardsService = inject(RewardsService);
  private router = inject(Router);

  // ========== SIGNALS ==========
  
  rewards = signal<Reward[]>([]);
  isLoading = signal(true);
  error = signal<string | null>(null);
  
  // Filtros
  filterActive = signal<'all' | 'active' | 'inactive'>('all');
  
  // Modales
  showCreateModal = signal(false);
  showEditModal = signal(false);
  editingReward = signal<Reward | null>(null);

  // ========== LIFECYCLE ==========

  ngOnInit(): void {
    this.loadRewards();
  }

  // ========== M\u00c9TODOS DE CARGA ==========

  loadRewards(): void {
    this.isLoading.set(true);
    this.error.set(null);

    const isActive = this.filterActive() === 'all' ? undefined : this.filterActive() === 'active';

    this.rewardsService.getAllRewards(isActive).subscribe({
      next: (response) => {
        this.rewards.set(response.rewards);
        this.isLoading.set(false);
      },
      error: (err) => {
        const detail = err.error?.detail || 'No se pudieron cargar las recompensas.';
        this.error.set(detail);
        this.isLoading.set(false);
      },
    });
  }

  // ========== M\u00c9TODOS DE NAVEGACI\u00d3N ==========

  goBack(): void {
    this.router.navigate(['/teacher-stats']);
  }

  // ========== M\u00c9TODOS DE MODAL ==========

  openCreateModal(): void {
    this.showCreateModal.set(true);
  }

  closeCreateModal(): void {
    this.showCreateModal.set(false);
  }

  openEditModal(reward: Reward): void {
    this.editingReward.set(reward);
    this.showEditModal.set(true);
  }

  closeEditModal(): void {
    this.editingReward.set(null);
    this.showEditModal.set(false);
  }

  // ========== M\u00c9TODOS DE CRUD ==========

  onRewardCreated(rewardData: RewardCreate): void {
    this.rewardsService.createReward(rewardData).subscribe({
      next: (response) => {
        console.log('\u2705 Recompensa creada:', response);
        this.closeCreateModal();
        this.loadRewards();
      },
      error: (err) => {
        const detail = err.error?.detail || 'Error al crear la recompensa.';
        alert(detail);
      },
    });
  }

  onRewardUpdated(rewardData: RewardUpdate): void {
    const rewardId = this.editingReward()?._id;
    if (!rewardId) return;

    this.rewardsService.updateReward(rewardId, rewardData).subscribe({
      next: (response) => {
        console.log('\u2705 Recompensa actualizada:', response);
        this.closeEditModal();
        this.loadRewards();
      },
      error: (err) => {
        const detail = err.error?.detail || 'Error al actualizar la recompensa.';
        alert(detail);
      },
    });
  }

  deleteReward(reward: Reward): void {
    const confirmed = confirm(`\u00bfEst\u00e1s seguro de eliminar la recompensa "${reward.title}"?`);
    if (!confirmed) return;

    this.rewardsService.deleteReward(reward._id).subscribe({
      next: (response) => {
        console.log('\u2705 Recompensa eliminada:', response);
        this.loadRewards();
      },
      error: (err) => {
        const detail = err.error?.detail || 'Error al eliminar la recompensa.';
        alert(detail);
      },
    });
  }

  toggleRewardStatus(reward: Reward): void {
    this.rewardsService.toggleRewardStatus(reward._id).subscribe({
      next: (response) => {
        console.log('\u2705 Estado de recompensa actualizado:', response);
        this.loadRewards();
      },
      error: (err) => {
        const detail = err.error?.detail || 'Error al cambiar el estado.';
        alert(detail);
      },
    });
  }

  // ========== M\u00c9TODOS DE FILTRO ==========

  setFilter(filter: 'all' | 'active' | 'inactive'): void {
    this.filterActive.set(filter);
    this.loadRewards();
  }

  getFilteredRewards(): Reward[] {
    const filter = this.filterActive();
    if (filter === 'all') return this.rewards();
    return this.rewards().filter(r => r.is_active === (filter === 'active'));
  }

  // ========== M\u00c9TODOS DE UTILIDAD ==========

  getRewardTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      'lesson_perfect': 'Lecci\u00f3n Perfecta',
      'streak_milestone': 'Hito de Racha',
      'xp_milestone': 'Hito de XP',
      'custom': 'Personalizada'
    };
    return labels[type] || type;
  }

  getRewardTypeColor(type: string): string {
    const colors: Record<string, string> = {
      'lesson_perfect': '#10b981',
      'streak_milestone': '#f59e0b',
      'xp_milestone': '#667eea',
      'custom': '#6b7280'
    };
    return colors[type] || '#6b7280';
  }
}
