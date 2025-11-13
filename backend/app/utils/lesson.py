from bson import ObjectId
from typing import Any


# Función auxiliar para convertir ObjectIds a strings recursivamente
def convert_object_ids_to_str(obj: Any) -> Any:
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, list):
        return [convert_object_ids_to_str(item) for item in obj]
    if isinstance(obj, dict):
        return {key: convert_object_ids_to_str(value) for key, value in obj.items()}
    return obj