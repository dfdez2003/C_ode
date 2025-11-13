from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from models import PyObjectId

class UserProgressAttempt(BaseModel):
    code: str
    is_correct: bool
    submitted_at: datetime

class UserProgressIn(BaseModel):
    exercise_id: PyObjectId
    code: str
    is_correct: bool
    session_id: PyObjectId

class UserProgressOut(BaseModel):
    id: str
    user_id: str
    exercise_id: str
    status: str
    attempts: List[UserProgressAttempt]
    last_session_id: Optional[str]
    is_mastered: bool

class UserProgressOut_Vvieja(BaseModel):
    id: PyObjectId
    user_id: PyObjectId
    exercise_id: PyObjectId
    status: str
    attempts: List[UserProgressAttempt]
    last_session_id: Optional[PyObjectId]
    is_mastered: bool