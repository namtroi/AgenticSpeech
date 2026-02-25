# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies via pip safely caching when unchanged
RUN pip install --no-cache-dir -r requirements.txt

# Set the python path to load the src module natively
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Copy the current directory contents into the container at /app
COPY src/ ./src/

# Run main.py when the container launches
CMD ["python", "src/main.py"]
