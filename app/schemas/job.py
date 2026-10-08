from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

class RecipientInput(BaseModel):
    name: str = Field(..., min_length=1)

class GenerationRequest(BaseModel):
    event_name: str = Field(..., min_length=1)
    event_date: str = Field(..., min_length=1)
    recipients: List[RecipientInput] = Field(..., min_length=1)

class JobResponse(BaseModel):
    job_id: str
    status: str
    total_recipients: int

class JobProgressResponse(BaseModel):
    job_id: str
    status: str
    total: int
    completed: int
    failed: int
    pending: int
    progress_percentage: float
