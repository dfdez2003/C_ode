export interface Auth {
}

/** Esquema de entrada para el registro de nuevos usuarios (Estudiante o Profesor) */
export interface UserCreate {
  username: string;
  email: string;
  password: string;
}

/** Esquema de entrada para el inicio de sesión */
export interface UserLogin {
  username: string;
  password: string;
}

/** Esquema de respuesta de FastAPI tras un login exitoso */
export interface Token {
  access_token: string;
  token_type: string; // Esperamos 'bearer'
}

/** Esquema de respuesta para la información del usuario actual (GET /users/me) */
export interface UserResponse {
  id: string; // ObjectId de MongoDB convertido a string [cite: 61, 70]
  username: string;
  email: string;
  role: 'student' | 'teacher'; // Roles definidos [cite: 62]
  created_at?: string; // Fecha en formato datetime [cite: 62]
  total_points?: number; // Puntos del usuario [cite: 62]
  // Campos adicionales del modelo User omitidos por simplicidad, pero pueden añadirse más tarde
}