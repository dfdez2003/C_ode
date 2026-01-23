// frontend/src/app/app.routes.ts

import { Routes } from '@angular/router';
import { RegisterComponent } from './pages/auth/register/register';
import { LoginComponent } from './pages/auth/login/login';
import { DashboardComponent } from './pages/dashboard/dashboard/dashboard';
import { authGuard } from './guards/auth-guard';
import { ListComponent } from './pages/modules/list/list';
import { DetailComponent } from './pages/modules/detail/detail';
import { GameMapComponent } from './pages/game-map/game-map';
import { LessonPageComponent } from './pages/lessons/lesson-page/lesson-page';
import { LessonEditorComponent } from './pages/lesson-editor/lesson-editor';
import { TeacherStatsComponent } from './pages/teacher-stats/teacher-stats';
import { StudentDashboardComponent } from './pages/student-dashboard/student-dashboard';
import { RewardsManagementComponent } from './pages/rewards-management/rewards-management';

export const routes: Routes = [
  // Rutas públicas de autenticación
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },
  
  // Ruta protegida principal: Mapa de Juego
  { 
    path: 'game-map', 
    component: GameMapComponent, 
    canActivate: [authGuard] 
  },
  
  // Ruta para editar lección (profesor)
  { 
    path: 'lesson-editor', 
    component: LessonEditorComponent, 
    canActivate: [authGuard] 
  },
  
  // Ruta para estadísticas del profesor
  { 
    path: 'teacher-stats', 
    component: TeacherStatsComponent, 
    canActivate: [authGuard] 
  },
  
  // Ruta para dashboard del estudiante
  { 
    path: 'student-dashboard', 
    component: StudentDashboardComponent, 
    canActivate: [authGuard] 
  },
  
  // Ruta para gestión de recompensas (profesor)
  { 
    path: 'rewards-management', 
    component: RewardsManagementComponent, 
    canActivate: [authGuard] 
  },
  
  // Ruta protegida (Dashboard - legacy, mantener por compatibilidad)
  { 
    path: 'dashboard', 
    component: ListComponent, 
    canActivate: [authGuard] 
  },
  
  // Ruta para el detalle del módulo
  { 
    path: 'module/:id', 
    component: DetailComponent, 
    canActivate: [authGuard] 
  },
  
  // Ruta para el detalle de lección (ejercicios) - NUEVA
  { 
    path: 'lessons/:id', 
    component: LessonPageComponent, 
    canActivate: [authGuard] 
  },
  
  // Redirección por defecto al login
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  
  // Catch-all para 404
  { path: '**', redirectTo: 'login' },
];