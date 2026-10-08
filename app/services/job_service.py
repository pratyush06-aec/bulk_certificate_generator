import logging
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import SessionLocal
from app.models.job import Job
from app.models.certificate import Certificate
from app.generators.certificate_generator import generate_certificate

logger = logging.getLogger(__name__)

def process_job_background(job_id: str, db: Session = None):
    logger.info(f"Background processing started for job: {job_id}")
    
    db_provided = db is not None
    db = db or SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return
            
        job.status = "PROCESSING"
        job.started_at = datetime.utcnow()
        db.commit()
        
        certificates = db.query(Certificate).filter(Certificate.job_id == job_id, Certificate.status == "PENDING").all()
        
        for cert in certificates:
            try:
                logger.info(f"Generating certificate {cert.id} for {cert.recipient_name}")
                file_path = generate_certificate(
                    recipient_name=cert.recipient_name,
                    event_name=job.event_name,
                    event_date=job.event_date,
                    certificate_id=cert.id,
                    job_id=job.id
                )
                
                cert.status = "COMPLETED"
                cert.file_path = file_path
                cert.completed_at = datetime.utcnow()
                db.commit()
                logger.info(f"Certificate {cert.id} completed successfully.")
                
            except Exception as e:
                logger.error(f"Failed to generate certificate {cert.id}: {e}")
                cert.status = "FAILED"
                cert.error_message = str(e)
                cert.completed_at = datetime.utcnow()
                db.commit()
                
        # Mark job as completed
        job.status = "COMPLETED"
        job.completed_at = datetime.utcnow()
        db.commit()
        logger.info(f"Job {job_id} processing completed.")
        
    except Exception as e:
        logger.error(f"Fatal error processing job {job_id}: {e}")
        if 'job' in locals() and job:
            job.status = "FAILED"
            db.commit()
    finally:
        if not db_provided:
            db.close()
