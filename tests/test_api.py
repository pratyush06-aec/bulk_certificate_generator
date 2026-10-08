import pytest
from app.models.job import Job
from app.models.certificate import Certificate
from unittest.mock import patch

def test_validation_errors(client):
    # Empty event name should fail validation
    res = client.post("/api/v1/jobs", json={
        "event_name": "",
        "event_date": "10 Oct 2026",
        "recipients": [{"name": "Test"}]
    })
    assert res.status_code == 422

    # Empty event_date should fail validation
    res_date = client.post("/api/v1/jobs", json={
        "event_name": "Test Event",
        "event_date": "",
        "recipients": [{"name": "Test"}]
    })
    assert res_date.status_code == 422

    # Empty recipient name should fail validation
    res_name = client.post("/api/v1/jobs", json={
        "event_name": "Test Event",
        "event_date": "10 Oct 2026",
        "recipients": [{"name": ""}]
    })
    assert res_name.status_code == 422

def test_create_job(client, db_session):
    with patch("app.api.routes.jobs.BackgroundTasks.add_task") as mock_bg_task:
        res = client.post("/api/v1/jobs", json={
            "event_name": "Test Event",
            "event_date": "10 Oct 2026",
            "recipients": [
                {"name": "Alice"}
            ]
        })
        assert res.status_code == 202
        data = res.json()
        assert "job_id" in data
        assert data["status"] == "QUEUED"
        assert data["total_recipients"] == 1
        
        mock_bg_task.assert_called_once()
        
        # Verify database inserts
        job = db_session.query(Job).filter(Job.id == data["job_id"]).first()
        assert job is not None
        assert job.event_name == "Test Event"
        
        certs = db_session.query(Certificate).filter(Certificate.job_id == data["job_id"]).all()
        assert len(certs) == 1
        assert certs[0].recipient_name == "Alice"

def test_job_status(client, db_session):
    job = Job(id="job123", event_name="Math Test", total_recipients=4, status="PROCESSING")
    db_session.add(job)
    
    db_session.add(Certificate(id="c1", job_id="job123", recipient_name="1", status="COMPLETED"))
    db_session.add(Certificate(id="c2", job_id="job123", recipient_name="2", status="COMPLETED"))
    db_session.add(Certificate(id="c3", job_id="job123", recipient_name="3", status="FAILED"))
    db_session.add(Certificate(id="c4", job_id="job123", recipient_name="4", status="PENDING"))
    db_session.commit()
    
    res = client.get("/api/v1/jobs/job123")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 4
    assert data["completed"] == 2
    assert data["failed"] == 1
    assert data["pending"] == 1
    # 3 processed out of 4 total -> 75%
    assert data["progress_percentage"] == 75.0

def test_failure_isolation(client, db_session):
    with patch("app.services.job_service.generate_certificate") as mock_generate:
        def side_effect(recipient_name, **kwargs):
            if recipient_name == "Fail":
                raise Exception("Intentional failure")
            return "/tmp/fake.pdf"
        mock_generate.side_effect = side_effect
        
        job = Job(id="job_fail_test", event_name="Fail Test", total_recipients=2)
        db_session.add(job)
        c1 = Certificate(id="c1", job_id=job.id, recipient_name="Pass", status="PENDING")
        c2 = Certificate(id="c2", job_id=job.id, recipient_name="Fail", status="PENDING")
        db_session.add_all([c1, c2])
        db_session.commit()
        
        from app.services.job_service import process_job_background
        process_job_background(job.id, db=db_session)
        
        db_session.refresh(c1)
        db_session.refresh(c2)
        db_session.refresh(job)
        
        assert c1.status == "COMPLETED"
        assert c2.status == "FAILED"
        assert "Intentional failure" in c2.error_message
        
        # Ensure job is still marked completed even though a certificate failed
        assert job.status == "COMPLETED"

def test_certificate_retrieval(client, db_session, tmp_path):
    import os
    fake_pdf = tmp_path / "test.pdf"
    fake_pdf.write_text("fake pdf content")
    
    cert = Certificate(id="cert1", job_id="job1", recipient_name="Test", status="COMPLETED", file_path=str(fake_pdf))
    db_session.add(cert)
    db_session.commit()
    
    res = client.get("/api/v1/certificates/cert1")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    
    # Missing certificate should 404
    res = client.get("/api/v1/certificates/invalid")
    assert res.status_code == 404

def test_generate_certificate_file():
    from app.generators.certificate_generator import generate_certificate
    import os
    
    job_id = "test_job_generation"
    cert_id = "test_cert_generation"
    
    # Execute the actual PIL drawing logic (no mocks)
    file_path = generate_certificate(
        recipient_name="Integration Test",
        event_name="Integration Event",
        event_date="31 Dec 2026",
        certificate_id=cert_id,
        job_id=job_id
    )
    
    # Verify the PDF was created
    assert os.path.exists(file_path)
    assert file_path.endswith(".pdf")
    assert os.path.getsize(file_path) > 0  # ensure it's not an empty file
    
    # Cleanup the test artifacts
    if os.path.exists(file_path):
        os.remove(file_path)
    
    job_dir = os.path.dirname(file_path)
    if os.path.exists(job_dir) and not os.listdir(job_dir):
        os.rmdir(job_dir)
