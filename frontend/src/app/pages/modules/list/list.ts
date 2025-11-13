// frontend/src/app/pages/modules/list/list.component.ts

import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ContentService } from '../../../services/content/content';
import { ModuleOut } from '../../../models/content'; 
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-list',
  standalone: true,
  imports: [CommonModule, RouterLink], // CommonModule para directivas como *ngFor, RouterLink para navegación
  templateUrl: './list.html',
  styleUrl: './list.css',
})
export class ListComponent implements OnInit {
  private contentService = inject(ContentService);

  public modules = signal<ModuleOut[]>([]);
  public isLoading = signal(true);
  public error = signal<string | null>(null);

  ngOnInit(): void {
    this.loadModules();
  }

  /**
   * Carga todos los módulos desde la API.
   */
  private loadModules(): void {
    this.isLoading.set(true);
    this.error.set(null);
    
    this.contentService.getModules().subscribe({
      next: (data) => {
        this.modules.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        const detail = err.error?.detail || 'No se pudieron cargar los módulos.';
        this.error.set(detail);
        this.isLoading.set(false);
      },
    });
  }
}