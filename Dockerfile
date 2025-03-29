FROM python:3.11-slim@sha256:d71b8eea6c9fcc6b25230361faf142c84f23ad4fbd1f852c8de96316a40a1add

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY docker-requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r docker-requirements.txt

# Copy application files
COPY *.py .
COPY .streamlit ./.streamlit
COPY attached_assets ./attached_assets
COPY test_deploy ./test_deploy

# Create necessary directories
RUN mkdir -p ./data

# Expose the single port for the combined app (proxy approach)
EXPOSE 5000

# Copy the startup script
COPY start.sh .
RUN chmod +x start.sh

# Command to run the combined service
CMD ["./start.sh"]