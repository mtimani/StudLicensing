# Use an official Python base image
FROM python:3.9-slim

# add /app to PYTHONPATH
# This allows Python to find the modules in the app directory
ENV PYTHONPATH=/app


# Install ImageMagick and its development libraries (MagickWand)
RUN apt-get update && apt-get install -y \
    imagemagick \
    libmagickwand-dev \
 && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy dependency definitions and install them
COPY ./requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

# Copy FastAPI application code into the container
COPY ./app/ /app

# Expose the port that FastAPI will run on
EXPOSE 8000

# Run the FastAPI application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

