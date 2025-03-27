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

# Expose the port Streamlit runs on
EXPOSE 5000

# Command to run the app
CMD ["streamlit", "run", "app.py", "--server.port=5000", "--server.address=0.0.0.0", "--logger.level=debug"]