from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

class RecipientInput(BaseModel):
    name: str

class GenerationRequest(BaseModel):
    event_name: str
    event_date: str
    recipients: List[RecipientInput]

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
