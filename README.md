<div align="center">
  <img src="static/favicon.png" alt="Logo" width="120" />
  <h1>Bulk Certificate Generator</h1>
  <p>A blazing fast, minimalist FastAPI backend and Vanilla JS frontend for asynchronously generating and serving certificates in bulk.</p>
</div>

---

## 📸 Screenshots

### Frontend UI
![Frontend Interface](file:///C:/Users/praty/.gemini/antigravity-ide/brain/c31d9139-b3bc-4506-8dc8-f3072981457a/.user_uploaded/media_1791566330321.png)

### Swagger API UI
![Swagger UI](file:///C:/Users/praty/.gemini/antigravity-ide/brain/c31d9139-b3bc-4506-8dc8-f3072981457a/.user_uploaded/media_1791460179422.png)

---

## 🏗️ Workflow & Architecture Documentation

This project outlines a complete decoupled architecture consisting of a modern, responsive frontend and a highly concurrent FastAPI backend that orchestrates the heavy lifting of bulk certificate generation using background tasks.

### System Architecture Overview
- **Frontend**: A vanilla HTML/CSS/JavaScript single-page application (SPA). It uses modern browser fetch APIs for asynchronous communication and dynamically updates the DOM based on backend responses.
- **Backend**: A robust REST API built with **FastAPI** and Python 3.
- **Database**: SQLite (via SQLAlchemy ORM) for tracking the status and metadata of certificate generation jobs.
- **Testing**: Playwright for end-to-end frontend testing and `pytest` for backend/integration testing.

### End-to-End Application Workflow
1. **User Input (Frontend)**: The user accesses `static/index.html`, inputs the Event Name and Date, and uploads a `.csv` or `.xlsx` Attendee Roster. Submitting sends a `POST` request to the backend.
2. **Job Initialization (Backend)**: The `/api/v1/jobs/upload` endpoint receives the file, creates a `PENDING` job in the SQLite DB, and starts a `BackgroundTasks` process. It instantly returns a `202 Accepted` with a `job_id`.
3. **Real-Time Polling**: The frontend uses the `job_id` to poll the `/api/v1/jobs/{job_id}` endpoint every 1.5 seconds, dynamically updating the progress bar and success/fail counters.
4. **Background Processing**: While polling occurs, the backend extracts the names from the spreadsheet, programmatically renders each certificate using templates (stamping the text onto the image), and logs success or failure metrics directly to the DB for each row.
5. **Archiving & Delivery**: Once all certificates are stamped, the backend zips the files into a single archive and sets the job to `COMPLETED`. The frontend stops polling, revealing a "Download ZIP" button which retrieves the final output via `/api/v1/jobs/{job_id}/download`.

---

## 🚀 Setup & Installation Commands

Follow these steps to set up the project locally.

### 1. Initial Setup
```bash
# Clone the repository and navigate into the project directory
# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate # Mac/Linux

# Install all backend dependencies
pip install -r requirements.txt

# (Optional) Create .env file for configuration overrides
# DATABASE_URL=sqlite:///./certificates.db
```

### 2. Running the Application
The application serves both the API and the Frontend together.

```bash
# Start the FastAPI server on port 8000
uvicorn app.main:app --reload
```

#### Playing with the Swagger UI
- Open your browser and navigate to: `http://localhost:8000/docs`
- Here you can inspect all endpoints, their expected schemas, and test them directly.

#### Playing with the Frontend UI
- Open your browser and navigate to: `http://localhost:8000/`
- This serves the `static/index.html` interface where you can drag-and-drop a spreadsheet and watch the dynamic progress bar as certificates generate.

---

## 🧪 Testing Guide

We have dedicated testing suites for both the backend (API) and the frontend (UI interactions). 

### Running Backend Tests
The backend tests ensure that endpoints, data validation, and asynchronous logic run perfectly using an in-memory SQLite database (`sqlite:///:memory:`).
```bash
# Ensure you are in the virtual environment
pytest tests/ -k "not test_frontend"
```

### Running Frontend Tests (Playwright)
The frontend UI is verified using end-to-end tests via Playwright, mocking backend responses to assure accurate DOM updates (progress bars, status changes).
```bash
# First, ensure Playwright browsers are installed
playwright install chromium

# Run only the frontend test suite
pytest tests/test_frontend.py
```

---

## 📜 Usage: Certificate Generation & Retrieval

The workflow can be engaged either via the Frontend UI or directly via the Swagger API.

### Via the Frontend (Recommended)
**Generation:**
1. Navigate to `http://localhost:8000/`.
2. Fill in the "Event Name" (e.g., *Tech Summit 2026*) and "Event Date" (e.g., *October 15, 2026*).
3. Upload your `.csv` or `.xlsx` attendee roster (Ensure it has a `name` column).
4. Click **Generate Certificates**. You will see the job status change to `PROCESSING` with real-time stats updating.

**Retrieval:**
1. Wait for the status badge to turn green and read `COMPLETED`.
2. Select your desired format (PDF or PNG) from the dropdown.
3. Click the **Download ZIP** button to retrieve all certificates.

### Via the Swagger UI (API-Level)
**Generation:**
1. Navigate to `http://localhost:8000/docs`.
2. Expand the `POST /api/v1/jobs/upload` endpoint and click **Try it out**.
3. Fill in the `event_name` and `event_date` string fields.
4. Upload your `.csv` or `.xlsx` file into the `file` field.
5. Execute. You will receive a response like `{"job_id": "uuid-string", "message": "Job accepted"}`.

**Retrieval:**
1. Expand the `GET /api/v1/jobs/{job_id}` endpoint and input your `job_id` to monitor the `progress_percentage` and status.
2. Once the status shows `"COMPLETED"`, expand the `GET /api/v1/jobs/{job_id}/download` endpoint.
3. Input your `job_id` and specify the `format` query parameter as `pdf` or `png`.
4. Click Execute, and click the **Download file** link in the response body to save your ZIP archive.

## 🐛 Known Bugs Encountered & Resolutions

During development, we encountered and resolved several interesting architectural and integration bugs:

1. **Schema Mismatch during Frontend Polling**: 
   - *Bug*: The frontend UI was remaining at 0% progress despite the backend successfully completing jobs. 
   - *Resolution*: Discovered a mismatch where `app.js` expected `data.total`, `data.completed`, and `data.status`, while the API returned `total_certificates`, `processed_certificates`, and lowercase status. We refactored the frontend UI test mocks and `app.js` to strictly parse the verified `JobProgressResponse` Pydantic schema and handle uppercase string comparisons.
2. **Duplicate FastAPI Keyword Arguments**: 
   - *Bug*: The application initially crashed with a `SyntaxError: keyword argument repeated` caused by passing `docs_url=None` twice in the `FastAPI()` instantiation.
   - *Resolution*: Removed the duplicate declaration in `app/main.py` to restore standard Swagger UI functionality.
3. **Frontend Horizontal Alignment Constraint**: 
   - *Bug*: The UI text sections were not spreading horizontally to fill the enterprise-grade wide layout, squishing the title and paragraph.
   - *Resolution*: Removed restrictive `max-width` properties in `styles.css` (`.intro-section`), allowing the text layout to inherit the full responsive `1200px` container width.
4. **Playwright Path Errors inside Windows Virtual Environment**: 
   - *Bug*: Running `pytest` for the Playwright frontend tests threw a `ModuleNotFoundError: No module named 'playwright'` despite successful pip installation, due to Windows PowerShell terminal sessions not fully inheriting `.venv` paths.
   - *Resolution*: Invoked pytest using explicitly resolved paths (`.\.venv\Scripts\pytest`) which correctly linked the binaries and successfully executed the E2E testing suite.
5. **Static File Resolution for Favicon**:
   - *Bug*: The favicon and other static assets failed to load natively because FastAPI did not properly serve the root static directory in some environments.
   - *Resolution*: Explicitly mounted the static folder using `app.mount("/static", StaticFiles(directory="static"), name="static")` ensuring the frontend templates and images served perfectly.

---

## ⚙️ Key System Design Decisions & Limitations

Through careful iteration, we made several foundational decisions:
- **Async Job Processing via Native BackgroundTasks**: Automatically handles background generation without relying on external task queues (like Celery or Redis). This reduces infrastructure complexity but limits true distributed scaling.
- **Fail-Safe Iteration & Error Isolation**: If one certificate rendering fails (e.g. invalid string encoding or empty row), the loop gracefully logs the failure into the SQLite database and continues the bulk job instead of crashing.
- **ZIP Strategy**: ZIP files are streamed in-memory (`io.BytesIO`) rather than persisted, significantly reducing disk bloat.
- **Frontend Agnosticism**: Playwright test cases dynamically target `#progressText` and `#jobStatusBadge` alongside network route interception (`page.route()`), making it highly resilient to backend data mutations.

**Current Limitations**:
- **Scaling Limit**: For massive events (>10,000 certificates), the in-memory streaming ZIP generation might hit RAM limits. In that case, transitioning to a temporary file-based zip chunking or S3 blob generation is advised.
- **Single Node State**: Because `BackgroundTasks` run in the same process memory space, stopping or restarting the server will kill actively processing jobs. Persistent, fault-tolerant message brokers (like RabbitMQ) would be required for enterprise-scale deployments.
