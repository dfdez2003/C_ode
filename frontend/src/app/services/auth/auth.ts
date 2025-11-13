
import { Injectable, signal, inject} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, switchMap, of } from 'rxjs'; 
import { environment } from '../../../environments/environments';
import { Token, UserCreate, UserLogin, UserResponse } from '../../models/auth';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  // Señal para almacenar el estado del usuario logueado
  public currentUser = signal<UserResponse | null>(null);
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl;

  constructor() {
    // Inicializa el usuario al cargar la app si hay un token
    // (Lógica de autologin se implementará más tarde, por ahora es un placeholder)
    this.checkInitialAuth();
  }
  // Nuevo método para verificar si hay un token al cargar la aplicación
  private checkInitialAuth(): void {
      if (localStorage.getItem('access_token')) {
          this.fetchCurrentUser().subscribe({
              error: () => this.logout() // Si el token expiró, cierra sesión
          });
      }
  }
  /**
   * Obtiene la información del usuario actual (rol incluido) de FastAPI.
   * Endpoint: GET /users/me (Ruta Protegida)
   */
  fetchCurrentUser(): Observable<UserResponse> {
      const url = `${this.apiUrl}/users/me`;
      return this.http.get<UserResponse>(url).pipe(
          tap(user => {
              this.currentUser.set(user); // Almacena el usuario en la señal
          })
      );
  }
  /**
   * Devuelve el objeto UserResponse almacenado en la señal (útil en Guards o templates).
   */
  getStoredUser(): UserResponse | null {
    return this.currentUser();
  }

  /**
   * Registra un nuevo usuario (Estudiante por defecto).
   * @param data - Credenciales del usuario.
   * @returns Observable de la respuesta de usuario.
   */
  register(data: UserCreate): Observable<UserResponse> {
    const url = `${this.apiUrl}/users/register`;
    return this.http.post<UserResponse>(url, data);
  }

  /**
   * Registra un nuevo profesor.
   * @param data - Credenciales del profesor.
   * @returns Observable de la respuesta de usuario.
   */
  registerTeacher(data: UserCreate): Observable<UserResponse> {
    const url = `${this.apiUrl}/users/register_teacher`;
    return this.http.post<UserResponse>(url, data);
  }

  /**
   * Inicia sesión, almacena el token, y llama a /users/me para obtener el rol.
   * Modificamos para encadenar la petición GET /users/me
   */
  login(credentials: UserLogin): Observable<UserResponse> {
    const url = `${this.apiUrl}/users/login`;
    
    return this.http.post<Token>(url, credentials).pipe(
      // 1. Almacena el token recibido
      tap((response: Token) => {
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('token_type', response.token_type);
      }),
      // 2. Encadena la llamada a /users/me para obtener los datos del usuario (incluido el rol)
      switchMap(() => this.fetchCurrentUser())
    );
  }

  /**
   * Cierra sesión y elimina el token.
   */
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    this.currentUser.set(null); // Limpia la señal del usuario
    // Implementar navegación a /login más adelante
  }
  // Pendiente: Método para obtener la información del usuario (/users/me)
}