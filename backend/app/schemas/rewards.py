from pydantic import BaseModel
from typing import List, Optional

class RewardIn(BaseModel):
    name: str
    description: str
    type: str
    points: int

class RewardOut(RewardIn):
    id: str
    users_awarded: List[str]

    