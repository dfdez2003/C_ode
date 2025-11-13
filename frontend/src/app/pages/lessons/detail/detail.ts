// frontend/src/app/pages/lessons/detail/detail.component.ts

import { Component, Input, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LessonOut } from '../../../models/content';
import { AuthService } from '../../../services/auth/auth';

@Component({
  selector: 'app-lesson-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './detail.html',
  styleUrl: './detail.css',
})
export class DetailComponent {
  private authService = inject(AuthService);
  
  // ✨ INPUT CLAVE: Recibe el objeto LessonOut del componente padre (ModuleDetailComponent)
  @Input({ required: true }) lesson!: LessonOut;
  @Input() moduleTitle: string = '';

  public userRole = this.authService.getStoredUser()?.role || 'student'; // Obtener el rol
}