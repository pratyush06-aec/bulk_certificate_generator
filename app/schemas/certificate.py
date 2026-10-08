from pydantic import BaseModel
from typing import Optional, List

class CertificateMetadataResponse(BaseModel):
    certificate_id: str
    recipient_name: str
    status: str
    error_message: Optional[str] = None
    download_url: Optional[str] = None

class JobCertificatesResponse(BaseModel):
    job_id: str
    certificates: List[CertificateMetadataResponse]
