// frontend/src/app/services/session/session.service.ts

import { Injectable, signal, effect, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { environment } from '../../../environments/environments';
import { firstValueFrom } from 'rxjs';

/**
 * 📦 Interfaces para Session
 */
export interface SessionResponse {
  id: string;
  user_id: string;
  start_time: string;
  end_time?: string;
  duration_minutes?: number;
}

/**
 *  SessionService - Gestión de Sesiones de Estudio
 * 
 * Funcionalidades:
 * - Iniciar sesión cuando el usuario comienza una lección
 * - Finalizar sesión cuando termina o cierra la app
 * - Tracking de tiempo en tiempo real
 * - Auto-guardado de sesión activa en localStorage
 */
@Injectable({
  providedIn: 'root'
})
export class SessionService {
  private http = inject(HttpClient);
  private router = inject(Router);

  // 🎯 Estado de la sesión actual
  public currentSessionId = signal<string | null>(null);
  public sessionStartTime = signal<Date | null>(null);
  public isSessionActive = signal<boolean>(false);

  // 📍 API Endpoint
  private readonly API_URL = `${environment.apiUrl}/sessions`;

  constructor() {
    // 🔄 Recuperar sesión activa al iniciar la app
    this.loadActiveSession();

    // 🛡️ Auto-finalizar sesión cuando el usuario cierra la pestaña/ventana
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.endSessionSync(); // Versión síncrona para beforeunload
      });
    }

    // 📊 Log de cambios de sesión (solo para debugging)
    effect(() => {
      if (this.currentSessionId()) {
        console.log('✅ Session Active:', this.currentSessionId());
      }
    });
  }

  /**
   * 🚀 Iniciar una nueva sesión de estudio
   * Se llama cuando el usuario entra a una lección
   */
  async startSession(): Promise<string> {
    try {
      // Si ya hay una sesión activa, devolverla
      if (this.currentSessionId()) {
        console.warn('⚠️ Ya existe una sesión activa:', this.currentSessionId());
        return this.currentSessionId()!;
      }

      const response = await firstValueFrom(
        this.http.post<SessionResponse>(`${this.API_URL}/start`, {})
      );

      // Actualizar el estado
      this.currentSessionId.set(response.id);
      this.sessionStartTime.set(new Date(response.start_time));
      this.isSessionActive.set(true);

      // Guardar en localStorage para recuperación
      this.saveActiveSession(response);

      console.log('✅ Sesión iniciada correctamente:', response.id);
      return response.id;

    } catch (error) {
      console.error('❌ Error al iniciar sesión:', error);
      
      // En caso de error, crear una sesión FAKE temporal
      const fakeId = `FAKE_SESSION_${Date.now()}`;
      this.currentSessionId.set(fakeId);
      this.sessionStartTime.set(new Date());
      this.isSessionActive.set(true);
      
      return fakeId;
    }
  }

  /**
   * 🛑 Finalizar la sesión de estudio actual
   * Se llama cuando el usuario completa la lección o sale
   */
  async endSession(): Promise<void> {
    const sessionId = this.currentSessionId();
    
    if (!sessionId) {
      console.warn('⚠️ No hay sesión activa para finalizar');
      return;
    }

    // Si es una sesión FAKE, solo limpiar el estado
    if (sessionId.startsWith('FAKE_SESSION_')) {
      this.clearSession();
      return;
    }

    try {
      await firstValueFrom(
        this.http.put<SessionResponse>(`${this.API_URL}/${sessionId}/end`, {})
      );

      console.log('✅ Sesión finalizada correctamente:', sessionId);
      this.clearSession();

    } catch (error) {
      console.error('❌ Error al finalizar sesión:', error);
      // Aunque falle, limpiamos el estado local
      this.clearSession();
    }
  }

  /**
   * 🔄 Versión síncrona de endSession para beforeunload
   * Usa navigator.sendBeacon para envío garantizado
   */
  private endSessionSync(): void {
    const sessionId = this.currentSessionId();
    
    if (!sessionId || sessionId.startsWith('FAKE_SESSION_')) {
      return;
    }

    // Usar sendBeacon para garantizar que la petición se envíe
    const url = `${this.API_URL}/${sessionId}/end`;
    const token = localStorage.getItem('access_token');
    
    if (token && navigator.sendBeacon) {
      // Beacon requiere Blob con headers
      const blob = new Blob([JSON.stringify({})], { 
        type: 'application/json' 
      });
      
      navigator.sendBeacon(url, blob);
      this.clearSession();
    }
  }

  /**
   * 📊 Obtener duración de la sesión actual en minutos
   */
  getSessionDuration(): number {
    const startTime = this.sessionStartTime();
    
    if (!startTime) {
      return 0;
    }

    const now = new Date();
    const diffMs = now.getTime() - startTime.getTime();
    return Math.floor(diffMs / 1000 / 60); // Minutos
  }

  /**
   * 📊 Obtener duración formateada (HH:MM:SS)
   */
  getFormattedDuration(): string {
    const startTime = this.sessionStartTime();
    
    if (!startTime) {
      return '00:00:00';
    }

    const now = new Date();
    const diffMs = now.getTime() - startTime.getTime();
    
    const hours = Math.floor(diffMs / 1000 / 60 / 60);
    const minutes = Math.floor((diffMs / 1000 / 60) % 60);
    const seconds = Math.floor((diffMs / 1000) % 60);

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }

  /**
   * 💾 Guardar sesión activa en localStorage
   */
  private saveActiveSession(session: SessionResponse): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('active_session', JSON.stringify({
        id: session.id,
        start_time: session.start_time
      }));
    }
  }

  /**
   * 📥 Cargar sesión activa desde localStorage al iniciar la app
   */
  private loadActiveSession(): void {
    if (typeof window === 'undefined') return;

    const savedSession = localStorage.getItem('active_session');
    
    if (savedSession) {
      try {
        const session = JSON.parse(savedSession);
        this.currentSessionId.set(session.id);
        this.sessionStartTime.set(new Date(session.start_time));
        this.isSessionActive.set(true);
        
        console.log('🔄 Sesión recuperada desde localStorage:', session.id);
      } catch (error) {
        console.error('❌ Error al recuperar sesión:', error);
        localStorage.removeItem('active_session');
      }
    }
  }

  /**
   * 🧹 Limpiar el estado de la sesión
   */
  private clearSession(): void {
    this.currentSessionId.set(null);
    this.sessionStartTime.set(null);
    this.isSessionActive.set(false);
    
    if (typeof window !== 'undefined') {
      localStorage.removeItem('active_session');
    }
  }

  /**
   * 🔍 Verificar si hay una sesión activa
   */
  hasActiveSession(): boolean {
    return this.isSessionActive() && this.currentSessionId() !== null;
  }
}
