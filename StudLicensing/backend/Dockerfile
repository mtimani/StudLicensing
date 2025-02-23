# Use an official Python base image
FROM python:3.13.2-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependency definitions and install them
COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy your FastAPI application code into the container
COPY ./app/ /app

# Expose the port that FastAPI will run on
EXPOSE 8000

# Run the FastAPI application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]