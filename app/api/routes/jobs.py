from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.job import Job
from app.models.certificate import Certificate
from app.schemas.job import GenerationRequest, JobResponse, JobProgressResponse
from app.schemas.certificate import CertificateMetadataResponse, JobCertificatesResponse
import uuid

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

from app.services.job_service import process_job_background

@router.post("", response_model=JobResponse, status_code=202)
def create_job(request: GenerationRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    
    new_job = Job(
        id=job_id,
        event_name=request.event_name,
        event_date=request.event_date,
        status="QUEUED",
        total_recipients=len(request.recipients)
    )
    db.add(new_job)
    
    for recipient in request.recipients:
        cert = Certificate(
            job_id=job_id,
            recipient_name=recipient.name,
            status="PENDING"
        )
        db.add(cert)
        
    db.commit()
    
    background_tasks.add_task(process_job_background, job_id)
    
    return JobResponse(
        job_id=job_id,
        status="QUEUED",
        total_recipients=new_job.total_recipients
    )

@router.get("/{job_id}", response_model=JobProgressResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    certs = db.query(Certificate).filter(Certificate.job_id == job_id).all()
    
    total = len(certs)
    completed = sum(1 for c in certs if c.status == "COMPLETED")
    failed = sum(1 for c in certs if c.status == "FAILED")
    pending = sum(1 for c in certs if c.status == "PENDING")
    
    processed = completed + failed
    progress = (processed / total * 100.0) if total > 0 else 0.0
    
    return JobProgressResponse(
        job_id=job.id,
        status=job.status,
        total=total,
        completed=completed,
        failed=failed,
        pending=pending,
        progress_percentage=progress
    )

@router.get("/{job_id}/certificates", response_model=JobCertificatesResponse)
def get_job_certificates(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    certs = db.query(Certificate).filter(Certificate.job_id == job_id).all()
    
    cert_responses = []
    for c in certs:
        cert_responses.append(
            CertificateMetadataResponse(
                certificate_id=c.id,
                recipient_name=c.recipient_name,
                status=c.status,
                error_message=c.error_message,
                download_url=f"/api/v1/certificates/{c.id}" if c.status == "COMPLETED" else None
            )
        )
        
    return JobCertificatesResponse(
        job_id=job.id,
        certificates=cert_responses
    )
