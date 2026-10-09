# Bulk Certificate Generator API

A blazing fast, minimalist FastAPI backend for asynchronously generating and serving certificates in bulk.

## Features
- **Async Job Processing**: Automatically handles background generation of bulk certificates using native FastAPI `BackgroundTasks`—no Celery or Redis required.
- **Spreadsheet Uploads**: Upload bulk attendee lists via `.csv` or `.xlsx` files without constructing JSON payloads.
- **Bulk ZIP Downloads**: Download all successfully generated certificates in one compressed `.zip` archive, in either high-quality `pdf` or `png` formats.
- **Failure Isolation**: If one certificate generation fails (or if a row is missing a name), the rest of the job continues gracefully and the job status resolves correctly.
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

1. **Create a Job (JSON)**: Send a `POST` request to `/api/v1/jobs` with the event details and recipients.
2. **Create a Job (Spreadsheet)**: Send a `POST` request to `/api/v1/jobs/upload` with an `event_name`, `event_date`, and a `.csv` or `.xlsx` file. The spreadsheet MUST have a `name` column.
3. **Check Status**: Poll `GET /api/v1/jobs/{job_id}` to monitor real-time completion percentages.
4. **Download Single Certificate**: Use `GET /api/v1/certificates/{cert_id}` to download a single `.pdf`.
5. **Download Bulk ZIP**: Once a job is completed, use `GET /api/v1/jobs/{job_id}/download?format=pdf` (or `format=png`) to download all valid certificates in a `.zip` archive. Note: Failed/invalid rows are excluded from the zip.

## Architectural Decisions & Limitations
- **PNG Conversions**: PNG ZIP files are created by rasterizing the original PDF certificates in-memory via `PyMuPDF`. This is an optimized standard over regenerating certificates from scratch.
- **ZIP Strategy**: ZIP files are streamed in-memory (`io.BytesIO`) rather than being persisted to disk, drastically reducing filesystem bloat and eliminating cron-job cleanups for temporary archives.
- **Row Parsing**: Empty `name` fields in a spreadsheet are treated as intentional validation failures immediately recorded in the database, meaning the API safely accepts them without halting the job and reports them in the failure metrics.
- **Scaling Limit**: For massive event jobs (>10,000 certificates), the in-memory streaming ZIP generation might hit RAM limits. In that case, transitioning to a temporary file-based zip chunking or S3 blob generation is advised.
