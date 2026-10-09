import io
import zipfile
import os
import pymupdf
from typing import Optional
from sqlalchemy.orm import Session
from app.models.certificate import Certificate

def create_job_archive(job_id: str, fmt: str, db: Session) -> Optional[io.BytesIO]:
    certs = db.query(Certificate).filter(Certificate.job_id == job_id, Certificate.status == "COMPLETED").all()
    
    if not certs:
        return None
        
    zip_buffer = io.BytesIO()
    
    used_filenames = set()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        files_added = 0
        for i, cert in enumerate(certs):
            if not cert.file_path or not os.path.exists(cert.file_path):
                continue
                
            safe_name = "".join([c if c.isalnum() else "_" for c in cert.recipient_name]).strip("_")
            if not safe_name:
                safe_name = f"certificate_{i}"
                
            base_filename = f"{safe_name}_{cert.id[:8]}"
            
            counter = 1
            filename = f"{base_filename}.{fmt}"
            while filename in used_filenames:
                filename = f"{base_filename}_{counter}.{fmt}"
                counter += 1
            used_filenames.add(filename)
            
            if fmt == "pdf":
                zip_file.write(cert.file_path, arcname=filename)
                files_added += 1
            elif fmt == "png":
                try:
                    doc = pymupdf.open(cert.file_path)
                    page = doc[0]
                    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                    img_bytes = pix.tobytes("png")
                    zip_file.writestr(filename, img_bytes)
                    doc.close()
                    files_added += 1
                except Exception:
                    pass
                    
        if files_added == 0:
            return None
            
    zip_buffer.seek(0)
    return zip_buffer
