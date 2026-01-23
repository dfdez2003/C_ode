// frontend/src/app/components/achievement-notification/achievement-notification.ts

import { Component, Input, Output, EventEmitter, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { trigger, state, style, transition, animate } from '@angular/animations';

@Component({
  selector: 'app-achievement-notification',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './achievement-notification.html',
  styleUrl: './achievement-notification.css',
  animations: [
    trigger('slideIn', [
      state('in', style({
        transform: 'translateY(0)',
        opacity: 1
      })),
      state('out', style({
        transform: 'translateY(-20px)',
        opacity: 0
      })),
      transition('out => in', [
        animate('500ms ease-in-out')
      ]),
      transition('in => out', [
        animate('300ms ease-in-out')
      ])
    ])
  ]
})
export class AchievementNotificationComponent {
  // 📥 Input: Array de logros
  @Input() achievements: string[] = [];
  
  // 📤 Output: Cuando el usuario cierra la notificación
  @Output() onClose = new EventEmitter<void>();

  // 🔄 Estado de visibilidad
  public isVisible = signal(false);
  public animationState = signal('out');

  constructor() {
    // Efecto: Cuando cambia achievements, mostrar notificación
    effect(() => {
      if (this.achievements && this.achievements.length > 0) {
        this.show();
      }
    });
  }

  /**
   * 👁️ Mostrar la notificación
   */
  private show(): void {
    this.isVisible.set(true);
    this.animationState.set('in');

    // Auto-ocultar después de 5 segundos
    setTimeout(() => {
      this.hide();
    }, 5000);
  }

  /**
   * 👁️ Ocultar la notificación
   */
  public hide(): void {
    this.animationState.set('out');
    
    setTimeout(() => {
      this.isVisible.set(false);
      this.onClose.emit();
    }, 300);
  }

  /**
   * 🎯 Obtener emoji según el logro
   */
  getEmojiForAchievement(achievement: string): string {
    // Extraer el emoji del principio del string (ej: "🎯 Logro")
    const emojiMatch = achievement.match(/^[\p{Emoji}]/u);
    return emojiMatch ? emojiMatch[0] : '⭐';
  }

  /**
   * 🎯 Obtener texto sin emoji
   */
  getTextWithoutEmoji(achievement: string): string {
    // Remover el emoji del principio
    return achievement.replace(/^[\p{Emoji}]\s*/u, '').trim();
  }

  /**
   * 🔄 TrackBy para lista de logros
   */
  trackByAchievement(index: number, achievement: string): string {
    return achievement;
  }
}
