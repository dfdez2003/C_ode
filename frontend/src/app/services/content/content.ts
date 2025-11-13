// frontend/src/app/services/content/content.service.ts

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environments';
import { ModuleOut, LessonOut } from '../../models/content';

@Injectable({
  providedIn: 'root',
})
export class ContentService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  /**
   * Obtiene la lista completa de módulos.
   * Endpoint: GET /modules/ [cite: 59]
   * Esta ruta es pública y no requiere autenticación[cite: 59].
   */
  getModules(): Observable<ModuleOut[]> {
    const url = `${this.apiUrl}/modules/`;
    return this.http.get<ModuleOut[]>(url);
  }

  /**
   * Obtiene un módulo específico por su ID.
   * El resultado incluye la lista de lecciones incrustadas.
   * Endpoint: GET /modules/{module_id} [cite: 59, 60]
   * Esta ruta es pública y no requiere autenticación[cite: 60].
   */
  getModuleById(moduleId: string): Observable<ModuleOut> {
    const url = `${this.apiUrl}/modules/${moduleId}`;
    return this.http.get<ModuleOut>(url);
  }

  /**
   * Obtiene una lección específica por su ID.
   * El resultado incluye la lista de ejercicios incrustados.
   * Endpoint: GET /lessons/{lesson_id} [cite: 60]
   * Esta ruta es pública y no requiere autenticación[cite: 60].
   */
  getLessonById(lessonId: string): Observable<LessonOut> {
    const url = `${this.apiUrl}/lessons/${lessonId}`;
    return this.http.get<LessonOut>(url);
  }

  // Pendiente: Métodos para obtener ejercicios, progreso, etc.
}