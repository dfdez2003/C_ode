import { HttpInterceptorFn } from '@angular/common/http';

/**
 * Interceptor para añadir el JWT (Bearer Token) a todas las peticiones HTTP.
 * El backend de FastAPI espera: Authorization: Bearer <token>
 */
export const tokenInterceptor: HttpInterceptorFn = (req, next) => {
  // 1. Obtener el token del almacenamiento local
  const token = localStorage.getItem('access_token');
  const tokenType = localStorage.getItem('token_type') || 'Bearer'; // Por defecto es Bearer

  console.log('🔐 TokenInterceptor ejecutado');
  console.log('  📍 URL:', req.url);
  console.log('  🔑 Token existe:', !!token);
  console.log('  🔑 Token (primeros 20 chars):', token ? token.substring(0, 20) + '...' : 'null');

  // 2. Si existe un token, clonar la petición y añadir el Header de Autorización
  if (token) {
    const authReq = req.clone({
      headers: req.headers.set('Authorization', `${tokenType} ${token}`),
    });
    console.log('  ✅ Header Authorization añadido:', authReq.headers.get('Authorization')?.substring(0, 30) + '...');
    // Pasa la nueva petición (con el token) al siguiente handler
    return next(authReq);
  }

  console.log('  ⚠️ No hay token, petición sin autenticación');
  // 3. Si no hay token, simplemente pasar la petición original (para login/register)
  return next(req);
};