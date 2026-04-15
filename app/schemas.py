from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=1)

class ProfileResponse(BaseModel):
    id: str
    name: str
    gender: str
    gender_probability: float
    sample_size: int
    age: int
    age_group: str
    country_id: str
    country_probability: float
    created_at: datetime

    # This allows Pydantic to populate the model from ORM objects directly
    class Config:
        from_attributes = True 

class SuccessResponse(BaseModel):
    status: str = "success"
    message: Optional[str] = None
    data: ProfileResponse

class ListResponse(BaseModel):
    status: str = "success"
    count: int
    data: List[ProfileResponse]