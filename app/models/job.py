import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import relationship
from app.db.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_name = Column(String, nullable=False)
    event_date = Column(String)
    status = Column(String, default="QUEUED")  # QUEUED, PROCESSING, COMPLETED, FAILED
    total_recipients = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    certificates = relationship("Certificate", back_populates="job")
