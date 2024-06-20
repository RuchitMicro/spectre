# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Create a non-root user
RUN useradd -m myuser

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Change ownership of the /app directory
RUN chown -R myuser:myuser /app

# Switch to the new user
USER myuser

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the command to start Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "mira.wsgi:application"]
