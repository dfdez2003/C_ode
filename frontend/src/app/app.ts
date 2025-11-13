import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from './services/auth/auth';
import { environment } from '../environments/environments';

@Component({
  selector: 'app-root',
  standalone: true, // Asegurar que es standalone
  imports: [RouterOutlet],
  template: `
    <router-outlet></router-outlet>
  `, 
  styleUrl: './app.css'



})
export class App {
  protected readonly title = signal('frontend');

  // Nueva propiedad para la URL
  public apiUrl: string = environment.apiUrl;

  // Inyectar el AuthService (solo para verificar que no haya errores de inyección)
  constructor() {
  }
}