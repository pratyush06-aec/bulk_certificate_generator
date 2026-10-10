from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.job import Job
from app.models.certificate import Certificate
from app.schemas.job import GenerationRequest, JobResponse, JobProgressResponse
from app.schemas.certificate import CertificateMetadataResponse, JobCertificatesResponse
import uuid

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

from app.services.job_service import process_job_background
from app.services.attendee_parser import parse_attendees_file
from app.services.archive_service import create_job_archive

@router.post("", response_model=JobResponse, status_code=202)
def create_job(request: GenerationRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not request.event_name.strip() or not request.event_date.strip():
        raise HTTPException(status_code=400, detail="event_name and event_date cannot be empty.")
        
    if not request.recipients:
        raise HTTPException(status_code=400, detail="No recipients provided.")

    job_id = str(uuid.uuid4())
    
    new_job = Job(
        id=job_id,
        event_name=request.event_name,
        event_date=request.event_date,
        status="QUEUED",
        total_recipients=len(request.recipients)
    )
    db.add(new_job)
    
    db.add_all([
        Certificate(
            job_id=job_id, 
            recipient_name=r.name, 
            status="PENDING" if r.name.strip() else "FAILED",
            error_message=None if r.name.strip() else "Recipient name cannot be empty"
        )
        for r in request.recipients
    ])
        
    db.commit()
    
    background_tasks.add_task(process_job_background, job_id)
    
    return JobResponse(
        job_id=job_id,
        status="QUEUED",
        total_recipients=new_job.total_recipients
    )

@router.post("/upload", response_model=JobResponse, status_code=202)
async def upload_job(
    background_tasks: BackgroundTasks,
    event_name: str = Form(...),
    event_date: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not event_name.strip() or not event_date.strip():
        raise HTTPException(status_code=400, detail="event_name and event_date cannot be empty.")
        
    raw_recipients = await parse_attendees_file(file)
    
    if not raw_recipients:
        raise HTTPException(status_code=400, detail="No recipients provided.")

    job_id = str(uuid.uuid4())
    
    new_job = Job(
        id=job_id,
        event_name=event_name,
        event_date=event_date,
        status="QUEUED",
        total_recipients=len(raw_recipients)
    )
    db.add(new_job)
    
    db.add_all([
        Certificate(
            job_id=job_id, 
            recipient_name=r.get("name", ""), 
            status="PENDING" if r.get("name", "").strip() else "FAILED",
            error_message=None if r.get("name", "").strip() else "Recipient name cannot be empty"
        )
        for r in raw_recipients
    ])
        
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
    
    cert_responses = [
        CertificateMetadataResponse(
            certificate_id=c.id,
            recipient_name=c.recipient_name,
            status=c.status,
            error_message=c.error_message,
            download_url=f"/api/v1/certificates/{c.id}" if c.status == "COMPLETED" else None
        )
        for c in certs
    ]
        
    return JobCertificatesResponse(
        job_id=job.id,
        certificates=cert_responses
    )

@router.get("/{job_id}/download")
def download_job_archive(job_id: str, format: str = "pdf", db: Session = Depends(get_db)):
    if format not in ["pdf", "png"]:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'pdf' or 'png'.")
        
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status not in ["COMPLETED", "FAILED"]:
        raise HTTPException(status_code=400, detail="Job is not yet complete. Cannot download archive.")
        
    zip_buffer = create_job_archive(job_id, format, db)
    
    if not zip_buffer:
        raise HTTPException(status_code=400, detail="No successful certificates available for download.")
        
    return StreamingResponse(
        zip_buffer, 
        media_type="application/zip", 
        headers={"Content-Disposition": f'attachment; filename="certificates_{job_id}_{format}.zip"'}
    )
