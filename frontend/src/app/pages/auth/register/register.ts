// frontend/src/app/pages/auth/register/register.component.ts

import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms'; // Importar módulos de formularios
import { Router } from '@angular/router';
import { AuthService } from '../../../services/auth/auth';
import { UserCreate } from '../../../models/auth';
// import { AuthService } from '../../../services/auth/auth.ts';
// import { UserCreate } from '../../../models/auth.ts';
// Importamos response y error para el manejo de respuestas y errores

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule], // Añadir ReactiveFormsModule
  // templateUrl: './register.component.html',
  templateUrl: './register.html',
  styleUrl: './register.css',
})
export class RegisterComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  // Variable para controlar si se está intentando registrar como profesor
  public isTeacherRegistration = signal(false); 
  public error = signal<string | null>(null);

  // Definición del formulario
  public registerForm = this.fb.group({
    username: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    secret_key: [''], // Campo para clave de profesor (inicialmente vacío)
  });

  constructor() {
    // Suscribirse a cambios en isTeacherRegistration para actualizar validadores
    // Esto es necesario porque Angular Signals no son reactivos automáticamente
    // Usamos un efecto implícito mediante el getter
  }

  /**
   * Getter para determinar si la clave secreta es requerida
   */
  get isSecretKeyRequired(): boolean {
    return this.isTeacherRegistration();
  }

  /**
   * Maneja el cambio del checkbox de profesor
   */
  public toggleTeacherRegistration(): void {
    const newValue = !this.isTeacherRegistration();
    this.isTeacherRegistration.set(newValue);
    
    const secretKeyControl = this.registerForm.get('secret_key');
    if (newValue) {
      // Si es profesor, la clave es requerida
      secretKeyControl?.setValidators([Validators.required, Validators.minLength(5)]);
    } else {
      // Si es estudiante, no es requerida
      secretKeyControl?.clearValidators();
    }
    secretKeyControl?.updateValueAndValidity();
  }

  /**
   * Maneja el envío del formulario.
   */
  public onSubmit(): void {
    this.error.set(null); // Limpiar errores previos
    if (this.registerForm.invalid) {
      this.error.set('Por favor, completa el formulario correctamente.');
      return;
    }

    const data: any = this.registerForm.value;

    let registration$: any;
    
    // Determinar qué endpoint llamar según la variable 'isTeacherRegistration'
    if (this.isTeacherRegistration()) {
      // Para profesor, enviamos con secret_key
      registration$ = this.authService.registerTeacher(data);
    } else {
      // Para estudiante, solo enviamos los campos básicos
      const studentData = {
        username: data.username,
        email: data.email,
        password: data.password
      };
      registration$ = this.authService.register(studentData);
    }

    registration$.subscribe({
      next: (response: any) => {
        // Registro exitoso. Se recomienda redirigir al login para obtener el token
        alert(`¡Registro exitoso! Rol: ${response.role}. Ahora inicia sesión.`);
        this.router.navigate(['/login']);
      },
      error: (err: any) => {
        // Manejo de errores de FastAPI (ej. usuario o email ya existe)
        const detail = err.error?.detail || 'Error desconocido al registrar.';
        this.error.set(detail);
      },
    });
  }
}