from fastapi import APIRouter, HTTPException
from bson import ObjectId  # Para validar IDs de MongoDB
from schemas.exercises import ExerciseCreate, ExerciseOut, ExerciseSchema
from services.exercises import (
    create_exercise_,
    get_exercise_strict
)
router = APIRouter(
    prefix="/exercises",
    tags=["exercises"]
)


@router.post("/create", response_model=ExerciseOut, status_code=201)
async def create_exercise(exercise_data: ExerciseCreate):
    try:
        # Llamar al servicio para crear el ejercicio
        new_ex = await create_exercise_(exercise_data)
        return new_ex
    except Exception as e:
        # Si hay cualquier error, retornar error 500 (Error interno del servidor)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{exercise_id}", response_model=ExerciseOut)
async def get_exercise(exercise_id: str):
    # Validar que el ID tenga el formato correcto de ObjectId de MongoDB
    if not ObjectId.is_valid(exercise_id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    # Buscar el ejercicio en la base de datos
    exercise = None# await get_exercise_by_id(exercise_id)
    
    # Si no se encuentra el ejercicio, retornar error 404
    if not exercise:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    
    return exercise


@router.get("/strict/{exercise_id}", response_model=ExerciseSchema)
async def get_exercise_typed(exercise_id: str):
    # Validar que el ID tenga el formato correcto de ObjectId
    if not ObjectId.is_valid(exercise_id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    try:
        # Obtener el ejercicio con validación estricta de tipo
        exercise = await get_exercise_strict(exercise_id)
        return exercise
    except Exception as e:
        # Si hay error de validación, retornar error 500 con detalles
        raise HTTPException(status_code=500, detail=f"Error validando tipo: {str(e)}")
