// frontend/src/app/guards/auth.guard.ts

import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';

/**
 * Función Guard para proteger rutas.
 * Permite el acceso (return true) si existe un 'access_token' en localStorage.
 * Redirige al login (return false) si no existe.
 */
export const authGuard: CanActivateFn = (route, state) => {
  // Inyectar el Router de forma funcional
  const router = inject(Router);

  // Intentar obtener el token del almacenamiento local
  const token = localStorage.getItem('access_token');

  if (token) {
    // Si hay un token, permite el acceso a la ruta (ej. /dashboard)
    return true;
  } else {
    // Si no hay token, redirige al usuario a la página de login
    // El 'replaceUrl: true' evita que el usuario pueda volver atrás con el botón del navegador
    router.navigate(['/login'], { replaceUrl: true });
    return false;
  }
};