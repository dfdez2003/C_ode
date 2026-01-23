// frontend/src/app/services/rewards/rewards.service.ts

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environments';

export interface Reward {
  _id: string;
  title: string;
  description: string;
  icon: string;
  reward_type: 'lesson_perfect' | 'streak_milestone' | 'xp_milestone' | 'custom';
  criteria?: any;
  xp_bonus: number;
  is_active: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface RewardCreate {
  title: string;
  description: string;
  icon: string;
  reward_type: string;
  criteria?: any;
  xp_bonus?: number;
  is_active?: boolean;
}

export interface RewardUpdate {
  title?: string;
  description?: string;
  icon?: string;
  reward_type?: string;
  criteria?: any;
  xp_bonus?: number;
  is_active?: boolean;
}

export interface RewardListResponse {
  total: number;
  rewards: Reward[];
}

@Injectable({
  providedIn: 'root'
})
export class RewardsService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/rewards`;

  /**
   * Obtiene todas las recompensas (para gestión del profesor)
   */
  getAllRewards(isActive?: boolean): Observable<RewardListResponse> {
    let url = `${this.apiUrl}/all`;
    if (isActive !== undefined) {
      url += `?is_active=${isActive}`;
    }
    console.log('🎁 HTTP GET Request (All Rewards):', url);
    return this.http.get<RewardListResponse>(url);
  }

  /**
   * Obtiene una recompensa específica por ID
   */
  getRewardById(rewardId: string): Observable<Reward> {
    const url = `${this.apiUrl}/${rewardId}`;
    console.log('🎁 HTTP GET Request (Reward Detail):', url);
    return this.http.get<Reward>(url);
  }

  /**
   * Crea una nueva recompensa
   */
  createReward(rewardData: RewardCreate): Observable<{ message: string; reward: Reward }> {
    const url = this.apiUrl;
    console.log('🎁 HTTP POST Request (Create Reward):', url, rewardData);
    return this.http.post<{ message: string; reward: Reward }>(url, rewardData);
  }

  /**
   * Actualiza una recompensa existente
   */
  updateReward(rewardId: string, rewardData: RewardUpdate): Observable<{ message: string; reward: Reward }> {
    const url = `${this.apiUrl}/${rewardId}`;
    console.log('🎁 HTTP PUT Request (Update Reward):', url, rewardData);
    return this.http.put<{ message: string; reward: Reward }>(url, rewardData);
  }

  /**
   * Elimina una recompensa
   */
  deleteReward(rewardId: string): Observable<{ message: string }> {
    const url = `${this.apiUrl}/${rewardId}`;
    console.log('🎁 HTTP DELETE Request (Delete Reward):', url);
    return this.http.delete<{ message: string }>(url);
  }

  /**
   * Activa/desactiva una recompensa
   */
  toggleRewardStatus(rewardId: string): Observable<{ message: string; reward: Reward }> {
    const url = `${this.apiUrl}/${rewardId}/toggle`;
    console.log('🎁 HTTP PATCH Request (Toggle Reward):', url);
    return this.http.patch<{ message: string; reward: Reward }>(url, {});
  }
}
