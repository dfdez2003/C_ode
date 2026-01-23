import { Component, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environments';
import { AuthService } from '../../services/auth/auth';

interface XPHistoryEntry {
  id: string;
  user_id: string;
  amount: number;
  reason: string;
  timestamp: string;
  reward_id?: string;
  lesson_id?: string;
  module_id?: string;
  metadata?: Record<string, any>;
}

interface XPHistoryResponse {
  user_id: string;
  count: number;
  limit: number;
  skip: number;
  history: XPHistoryEntry[];
}

interface XPSummary {
  total_xp: number;
  total_transactions: number;
  breakdown_by_reason: Record<string, number>;
}

@Component({
  selector: 'app-xp-history',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './xp-history.html',
  styleUrls: ['./xp-history.css']
})
export class XPHistoryComponent {
  private http = inject(HttpClient);
  private authService = inject(AuthService);
  private apiUrl = environment.apiUrl;
  
  // Exponer Object para usarlo en el template
  Object = Object;
  
  // Signals
  userId = signal<string>('');
  history = signal<XPHistoryEntry[]>([]);
  summary = signal<XPSummary | null>(null);
  loading = signal(false);
  error = signal<string | null>(null);
  
  // Paginación
  currentPage = signal(0);
  pageSize = signal(20);
  totalCount = signal(0);

  constructor() {
    effect(() => {
      const user = this.authService.currentUser();
      if (user && user.id) {
        this.userId.set(user.id);
        this.loadHistory();
        this.loadSummary();
      }
    });
  }

  loadHistory(): void {
    this.loading.set(true);
    this.error.set(null);
    
    const skip = this.currentPage() * this.pageSize();
    const url = `${this.apiUrl}/xp-history/user/${this.userId()}/history?limit=${this.pageSize()}&skip=${skip}`;
    
    this.http.get<XPHistoryResponse>(url).subscribe({
      next: (response) => {
        this.history.set(response.history);
        this.totalCount.set(response.count);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error loading XP history:', err);
        this.error.set('Error al cargar el historial de XP');
        this.loading.set(false);
      }
    });
  }

  loadSummary(): void {
    const url = `${this.apiUrl}/xp-history/user/${this.userId()}/summary`;
    
    this.http.get<XPSummary>(url).subscribe({
      next: (summary) => {
        this.summary.set(summary);
      },
      error: (err) => {
        console.error('Error loading XP summary:', err);
      }
    });
  }

  getReasonLabel(reason: string): string {
    const labels: Record<string, string> = {
      'lesson_completion': '📚 Lección Completada',
      'perfection_bonus': '⭐ Bono de Perfección',
      'reward_awarded': '🏆 Recompensa Otorgada',
      'streak_bonus': '🔥 Bono de Racha',
      'manual_adjustment': '⚙️ Ajuste Manual'
    };
    return labels[reason] || reason;
  }

  getReasonColor(reason: string): string {
    const colors: Record<string, string> = {
      'lesson_completion': '#4CAF50',
      'perfection_bonus': '#FFB800',
      'reward_awarded': '#2196F3',
      'streak_bonus': '#FF5722',
      'manual_adjustment': '#9C27B0'
    };
    return colors[reason] || '#888';
  }

  previousPage(): void {
    if (this.currentPage() > 0) {
      this.currentPage.update(p => p - 1);
      this.loadHistory();
    }
  }

  nextPage(): void {
    if ((this.currentPage() + 1) * this.pageSize() < this.totalCount()) {
      this.currentPage.update(p => p + 1);
      this.loadHistory();
    }
  }

  formatDate(isoString: string): string {
    const date = new Date(isoString);
    return date.toLocaleString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  hasNextPage(): boolean {
    return (this.currentPage() + 1) * this.pageSize() < this.totalCount();
  }

  // Helper para acceder a metadata de forma segura
  getMetadataValue(metadata: Record<string, any> | undefined, key: string): any {
    return metadata?.[key];
  }

  hasMetadataKey(metadata: Record<string, any> | undefined, key: string): boolean {
    return !!metadata?.[key];
  }
}

