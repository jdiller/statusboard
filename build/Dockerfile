# Use the official Python image from the Docker Hub
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy the requirements file into the image
COPY requirements.txt /app/

# Install system dependencies and Liberation Sans font
RUN apt-get update && apt-get install -y --no-install-recommends \
    fontconfig \
    fonts-liberation \
    fonts-terminus \
    curl \
    && fc-cache -f -v \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the image
COPY . /app/

# Ensure the assets folder is copied
COPY assets /app/assets

# Expose the port the app runs on
EXPOSE 5000

ENV TZ="America/Toronto"

# Run the application with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]