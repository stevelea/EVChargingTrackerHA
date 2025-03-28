FROM python:3.11-slim

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

# Create data directory
RUN mkdir -p ./data

# Copy application files
COPY *.py .
COPY .streamlit ./.streamlit

# Expose the ports for both Streamlit and API server
EXPOSE 5000 5001

# Copy the startup script
COPY start.sh .
RUN chmod +x start.sh

# Command to run both services
CMD ["./start.sh"]