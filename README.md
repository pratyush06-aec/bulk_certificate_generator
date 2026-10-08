# Bulk Certificate Generator API

A blazing fast, minimalist FastAPI backend for asynchronously generating and serving certificates in bulk.

## Features
- **Async Job Processing**: Automatically handles background generation of bulk certificates using native FastAPI `BackgroundTasks`—no Celery or Redis required.
- **Failure Isolation**: If one certificate generation fails, the rest of the job continues gracefully and the job status resolves correctly.
- **Dynamic Template Stamping**: Uses standard `Pillow` to precisely stamp variables (Recipient Name, Event, Date, ID) over a pre-designed template.
- **No Bloat**: No headless chrome or heavy HTML renderers; pure native coordinate-based text rendering.
- **Robust Testing**: Complete pytest suite covering validation, processing, isolation, and status mathematics, mapped to an isolated in-memory SQLite instances using `StaticPool`.

## Setup

1. **Install Dependencies**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Create a `.env` file in the root based on `.env.example`:
   ```env
   DATABASE_URL=postgresql://your_db_url_here
   CERTIFICATE_STORAGE_PATH=./generated
   ```

3. **Database Migrations**
   ```bash
   alembic upgrade head
   ```

4. **Run the Server**
   ```bash
   uvicorn app.main:app --reload
   ```

## Usage

Navigate to `http://localhost:8000/docs` to use the interactive Swagger UI.

1. **Create a Job**: Send a `POST` request to `/api/v1/jobs` with the event details and recipients.
2. **Check Status**: Poll `/api/v1/jobs/{job_id}` to monitor real-time completion percentages.
3. **Download**: Once completed, use the `/api/v1/certificates/{cert_id}` endpoint to download the generated `.pdf`.
