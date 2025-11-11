# Base image
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE 1  # disables .pyc files
ENV PYTHONUNBUFFERED 1         # output appears immediately

# Create a non-root user and group
RUN groupadd -r solarize && useradd -r -g solarize -ms /bin/bash solarize

# Set working directory and switch to non-root user
WORKDIR /solarize
USER solarize

# Copy requirements first for caching
COPY --chown=solarize:solarize requirements.txt .

# Install Python dependencies without cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project into the container
COPY --chown=solarize:solarize . .

# Expose Daphne port internally for Nginx to reach
EXPOSE 8000

# Command to start Daphne
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "solarize.asgi:application"]

