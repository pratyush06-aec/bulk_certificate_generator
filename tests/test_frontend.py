import pytest
import threading
import time
import uvicorn
import requests
from playwright.sync_api import Page, expect

def run_server():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, log_level="critical")

@pytest.fixture(scope="session", autouse=True)
def test_server():
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for the server to be ready
    for _ in range(50):
        try:
            response = requests.get("http://127.0.0.1:8001/")
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            time.sleep(0.1)
    else:
        pytest.fail("Test server failed to start")
        
    yield

def test_frontend_data_fetching(page: Page):
    """
    Test the frontend data fetching using Playwright by mocking the API responses.
    """
    # Navigate to the frontend
    page.goto("http://127.0.0.1:8001/")
    
    # Check if the title is correct
    expect(page).to_have_title("Bulk Certificate Generator")
    
    # Mock the job upload endpoint
    def handle_upload(route):
        route.fulfill(
            status=202,
            json={"job_id": "test-job-123", "message": "Job accepted"}
        )
    page.route("**/api/v1/jobs/upload", handle_upload)
    
    # Mock the job polling endpoint
    def handle_poll(route):
        route.fulfill(
            status=200,
            json={
                "job_id": "test-job-123",
                "status": "PROCESSING",
                "total": 10,
                "completed": 4,
                "failed": 1,
                "pending": 5,
                "progress_percentage": 50.0
            }
        )
    page.route("**/api/v1/jobs/test-job-123", handle_poll)
    
    # Mock the errors endpoint
    def handle_errors(route):
        route.fulfill(
            status=200,
            json={
                "certificates": [
                    {"recipient_name": "mockerror@test.com", "status": "FAILED", "error_message": "Invalid template format"}
                ]
            }
        )
    page.route("**/api/v1/jobs/test-job-123/certificates", handle_errors)

    # 1. Fill event name and date
    page.fill("#eventName", "Playwright Test Event")
    page.fill("#eventDate", "2026-10-10")
    
    # 2. Add fake files to the file inputs
    page.set_input_files("#fileInput", {"name": "test.xlsx", "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "buffer": b"dummy"})
    
    # 3. Click the submit button
    page.click("button[type='submit']")
    
    # 4. Wait and assert that the UI updates correctly based on the mocked fetch data
    expect(page.locator("#progressText")).to_have_text("50%")
    expect(page.locator("#statTotal")).to_have_text("10")
    expect(page.locator("#statSuccess")).to_have_text("4")
    expect(page.locator("#statFailed")).to_have_text("1")
    
    # 5. Assert that the error list displays our mocked error
    expect(page.locator("#errorList li")).to_contain_text("mockerror@test.com: Invalid template format")

    # Let's mock completion
    def handle_poll_completed(route):
        route.fulfill(
            status=200,
            json={
                "job_id": "test-job-123",
                "status": "COMPLETED",
                "total": 10,
                "completed": 9,
                "failed": 1,
                "pending": 0,
                "progress_percentage": 100.0,
                "zip_file_path": "dummy.zip"
            }
        )
    page.unroute("**/api/v1/jobs/test-job-123")
    page.route("**/api/v1/jobs/test-job-123", handle_poll_completed)

    # 6. Assert UI updates for completion
    expect(page.locator("#progressText")).to_have_text("100%")
    expect(page.locator("#jobStatusBadge")).to_have_text("COMPLETED")
