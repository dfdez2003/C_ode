// frontend/src/app/pages/auth/login/login.component.ts

import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms'; // Importar formularios
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../services/auth/auth'; // Importar servicio
import { UserLogin } from '../../../models/auth'; // Importar modelo

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink], // Añadir ReactiveFormsModule y RouterLink
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  public error = signal<string | null>(null);

  // Definición del formulario
  public loginForm = this.fb.group({
    username: ['', [Validators.required]],
    password: ['', [Validators.required]],
  });

  /**
   * Maneja el envío del formulario.
   */
  public onSubmit(): void {
    this.error.set(null);
    if (this.loginForm.invalid) {
      this.error.set('Por favor, introduce tu usuario y contraseña.');
      return;
    }

    const credentials: UserLogin = this.loginForm.value as UserLogin;

    this.authService.login(credentials).subscribe({
      next: (response) => {
        // Token almacenado en localStorage dentro del .pipe(tap()) del AuthService
        alert(`Inicio de sesión exitoso. Redirigiendo...`);
        this.router.navigate(['/game-map']); // Redirigir al mapa de juego
      },
      error: (err) => {
        // Manejo de errores de FastAPI (ej. 401 Unauthorized)
        const detail = err.error?.detail || 'Credenciales incorrectas o error desconocido.';
        this.error.set(detail);
      },
    });
  }
}