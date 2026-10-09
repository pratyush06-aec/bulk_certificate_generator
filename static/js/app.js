document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const fileMsg = document.querySelector('.file-msg');
    const form = document.getElementById('jobForm');
    const submitBtn = document.getElementById('submitBtn');
    
    const statusSection = document.getElementById('statusSection');
    const jobStatusBadge = document.getElementById('jobStatusBadge');
    const statTotal = document.getElementById('statTotal');
    const statSuccess = document.getElementById('statSuccess');
    const statFailed = document.getElementById('statFailed');
    const progressBar = document.getElementById('progressBar');
    
    const downloadSection = document.getElementById('downloadSection');
    const downloadBtn = document.getElementById('downloadBtn');
    const downloadFormat = document.getElementById('downloadFormat');

    const errorListContainer = document.getElementById('errorListContainer');
    const errorList = document.getElementById('errorList');

    let currentJobId = null;
    let pollInterval = null;
    let lastFailedCount = 0;

    // File Input styling
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileMsg.textContent = e.target.files[0].name;
            fileMsg.style.color = 'var(--color-primary)';
            fileMsg.style.fontWeight = '500';
        } else {
            fileMsg.textContent = 'Choose a file or drag it here';
            fileMsg.style.color = 'var(--color-text-secondary)';
            fileMsg.style.fontWeight = '400';
        }
    });

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const eventName = document.getElementById('eventName').value;
        const eventDate = document.getElementById('eventDate').value;
        const file = fileInput.files[0];

        if (!file) return;

        submitBtn.disabled = true;
        submitBtn.textContent = 'Uploading...';

        const formData = new FormData();
        formData.append('event_name', eventName);
        formData.append('event_date', eventDate);
        formData.append('file', file);

        try {
            const response = await fetch('/api/v1/jobs/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Upload failed');
            }

            const data = await response.json();
            currentJobId = data.job_id;
            lastFailedCount = 0; // Reset tracking
            
            // Show status section
            statusSection.style.display = 'block';
            downloadSection.style.display = 'none';
            errorListContainer.style.display = 'none';
            errorList.innerHTML = '';
            
            // Reset stats
            updateStats({ status: 'PENDING', total_certificates: 0, successful: 0, failed: 0 });
            
            // Start polling
            if (pollInterval) clearInterval(pollInterval);
            pollInterval = setInterval(pollStatus, 1500);
            
        } catch (err) {
            alert(err.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Generate Certificates';
            form.reset();
            fileMsg.textContent = 'Choose a file or drag it here';
            fileMsg.style.color = 'var(--color-text-secondary)';
            fileMsg.style.fontWeight = '400';
        }
    });

    async function pollStatus() {
        if (!currentJobId) return;

        try {
            const response = await fetch(`/api/v1/jobs/${currentJobId}`);
            if (!response.ok) throw new Error('Failed to fetch status');
            
            const data = await response.json();
            updateStats(data);
            
            if (data.failed > 0 && data.failed !== lastFailedCount) {
                lastFailedCount = data.failed;
                // Fetch the detailed errors dynamically
                const certResponse = await fetch(`/api/v1/jobs/${currentJobId}/certificates`);
                if (certResponse.ok) {
                    const certData = await certResponse.json();
                    updateErrors(certData.certificates);
                }
            }

            if (data.status === 'COMPLETED' || data.status === 'FAILED') {
                clearInterval(pollInterval);
                if (data.completed > 0) {
                    downloadSection.style.display = 'block';
                }
            }
        } catch (err) {
            console.error(err);
        }
    }

    function updateStats(data) {
        jobStatusBadge.textContent = data.status;
        jobStatusBadge.className = `badge ${data.status}`;
        
        const total = data.total || 0;
        const success = data.completed || 0;
        const failed = data.failed || 0;
        
        statTotal.textContent = total;
        statSuccess.textContent = success;
        statFailed.textContent = failed;

        const processed = success + failed;
        let pct = 0;
        if (total > 0) {
            pct = (processed / total) * 100;
        }
        progressBar.style.width = `${pct}%`;
        
        const progressText = document.getElementById('progressText');
        if (progressText) {
            progressText.textContent = `${Math.round(pct)}%`;
        }
    }

    function updateErrors(certificates) {
        const failedCerts = certificates.filter(c => c.status === 'FAILED');
        if (failedCerts.length > 0) {
            errorListContainer.style.display = 'block';
            errorList.innerHTML = '';
            failedCerts.forEach(cert => {
                const li = document.createElement('li');
                // Clean up technical traceback looking string to just the message
                let errorMsg = cert.error_message || 'Unknown error';
                li.textContent = `${cert.recipient_name}: ${errorMsg}`;
                errorList.appendChild(li);
            });
        } else {
            errorListContainer.style.display = 'none';
        }
    }

    downloadBtn.addEventListener('click', () => {
        if (!currentJobId) return;
        const format = downloadFormat.value;
        window.location.href = `/api/v1/jobs/${currentJobId}/download?format=${format}`;
    });
});
