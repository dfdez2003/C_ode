from fastapi import FastAPI
from routers import users, modules, sessions, progress, rewards, xp_history
from fastapi.middleware.cors import CORSMiddleware

# Instancia de la aplicación FastAPI
app = FastAPI(
    title="Aprendiendo C - API",
    description="API para una aplicación de aprendizaje de C tipo Duolingo.",
    version="1.0.0",
)
# Configuración de CORS para permitir peticiones desde el frontend Angular
origins = [
    # El origen de tu frontend Angular
    "http://localhost:4200", 
    # Origen adicional si es necesario
    "http://127.0.0.1:4200",
]
# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Permitir peticiones solo desde Angular
    allow_credentials=True, # Permitir cookies (no es necesario para JWT, pero buena práctica)
    allow_methods=["*"],    # Permitir todos los métodos (GET, POST, PUT, DELETE)
    allow_headers=["*"],    # Permitir todos los headers (incluido 'Authorization')
)

# Ruta raíz para verificar que la API está funcionando
@app.get("/", tags=["root"])
async def read_root():
    return {"message": "¡Bienvenido a la API de Aprendiendo C!"}

# Incluir los routers de los diferentes módulos
app.include_router(users.router)
app.include_router(modules.router)
app.include_router(sessions.router)
app.include_router(progress.router)
app.include_router(rewards.router)
app.include_router(xp_history.router)