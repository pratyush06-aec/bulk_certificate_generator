import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.certificate import Certificate

router = APIRouter(prefix="/api/v1/certificates", tags=["Certificates"])

@router.get("/{certificate_id}")
def download_certificate(certificate_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
        
    if cert.status == "PENDING":
        raise HTTPException(status_code=400, detail="Certificate is still pending")
    elif cert.status == "FAILED":
        raise HTTPException(status_code=400, detail=f"Certificate generation failed: {cert.error_message}")
        
    if not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate file not found on disk")
        
    return FileResponse(
        path=cert.file_path,
        filename=f"certificate_{cert.recipient_name.replace(' ', '_')}.pdf",
        media_type="application/pdf"
    )
