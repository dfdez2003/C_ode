import { HttpInterceptorFn } from '@angular/common/http';

/**
 * Interceptor para añadir el JWT (Bearer Token) a todas las peticiones HTTP.
 * El backend de FastAPI espera: Authorization: Bearer <token>
 */
export const tokenInterceptor: HttpInterceptorFn = (req, next) => {
  // 1. Obtener el token del almacenamiento local
  const token = localStorage.getItem('access_token');
  const tokenType = localStorage.getItem('token_type') || 'Bearer'; // Por defecto es Bearer

  // 2. Si existe un token, clonar la petición y añadir el Header de Autorización
  if (token) {
    const authReq = req.clone({
      headers: req.headers.set('Authorization', `${tokenType} ${token}`),
    });
    // Pasa la nueva petición (con el token) al siguiente handler
    return next(authReq);
  }

  // 3. Si no hay token, simplemente pasar la petición original (para login/register)
  return next(req);
};