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

  console.log('🛡️ AuthGuard ejecutado');
  console.log('  📍 Ruta solicitada:', state.url);
  console.log('  🔑 Token existe:', !!token);
  console.log('  🔑 Token (primeros 20):', token ? token.substring(0, 20) + '...' : 'null');

  if (token) {
    // Si hay un token, permite el acceso a la ruta (ej. /dashboard)
    console.log('  ✅ Acceso permitido');
    return true;
  } else {
    // Si no hay token, redirige al usuario a la página de login
    // El 'replaceUrl: true' evita que el usuario pueda volver atrás con el botón del navegador
    console.log('  ❌ Sin token, redirigiendo al login');
    router.navigate(['/login'], { replaceUrl: true });
    return false;
  }
};