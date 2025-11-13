from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from models import PyObjectId

class SessionIn(BaseModel):
    user_id: PyObjectId

class SessionOut(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    exercises_completed: List[str]
    total_points_gained: int

class SessionOut_Vvieja(BaseModel):
    id: PyObjectId
    user_id: PyObjectId
    start_time: datetime
    end_time: Optional[datetime]
    exercises_completed: List[PyObjectId]
    total_points_gained: int

class SessionStart(BaseModel):
    lesson_id: PyObjectId

class SessionComplete(BaseModel):
    total_points_gained: int = 0
    exercises_completed: int = 0



