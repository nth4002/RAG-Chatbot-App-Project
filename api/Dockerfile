# api/Dockerfile

# Use the specific Python version requested. Use slim for smaller size.
FROM python:3.12.3-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies if any of your Python packages need them
# Example: RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && rm -rf /var/lib/apt/lists/*

# Copy ONLY the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies specified in requirements.txt
# --no-cache-dir helps keep the image smaller
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your backend application code into the container
COPY . .

# Expose the port that FastAPI/Uvicorn will run on
EXPOSE 8000

# The command to run when the container starts
# Use 0.0.0.0 to make it accessible from outside the container network
# DO NOT use --reload in production images
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]