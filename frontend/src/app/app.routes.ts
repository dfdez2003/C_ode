// frontend/src/app/app.routes.ts

import { Routes } from '@angular/router';
import { RegisterComponent } from './pages/auth/register/register';
import { LoginComponent } from './pages/auth/login/login';
import { DashboardComponent } from './pages/dashboard/dashboard/dashboard';
import { authGuard } from './guards/auth-guard';
import { ListComponent } from './pages/modules/list/list';
import { DetailComponent } from './pages/modules/detail/detail'; // Importar el nuevo componente
// Nota: Aún no creamos el AuthGuard, lo haremos en el siguiente paso

export const routes: Routes = [
  // Rutas públicas de autenticación
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  
  // Ruta protegida (Dashboard)
  { 
    path: 'dashboard', 
    // Usamos el ListComponent como la vista principal de la aplicación
    component: ListComponent, 
    canActivate: [authGuard] 
  },
  // Ruta para el detalle del módulo (Necesaria para la navegación)
  { 
    path: 'module/:id', 
    // Usaremos un componente que crearemos después para mostrar el detalle
    // Por ahora, temporalmente apuntamos al mismo ListComponent para evitar errores de ruta
    component: DetailComponent, 
    canActivate: [authGuard] 
  },
  { 
    path: 'lesson/:id', 
    // Usaremos el componente DetailComponent TEMPORALMENTE
    // Lo reemplazaremos con LessonDetailComponent en la Fase 3.0
    component: DetailComponent, 
    canActivate: [authGuard] 
  },
  
  // Redirección por defecto
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  
  // Catch-all para 404
  { path: '**', redirectTo: 'login' },
  // Ruta de Detalle de Módulo
  { 
    path: 'module/:id', 
    component: DetailComponent, // Usar el componente DetailComponent
    canActivate: [authGuard] 
  },

];