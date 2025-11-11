# Base image: slim Python
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create non-root user and group
RUN groupadd -r solarize && useradd -r -g solarize -ms /bin/bash solarize

# Set working directory
WORKDIR /solarize

# Pre-create staticfiles directory for mounting
RUN mkdir -p /solarize/staticfiles /solarize/media \
    && chown -R solarize:solarize /solarize/staticfiles /solarize/media

# Switch to non-root user
USER solarize

# Copy requirements and install dependencies
COPY --chown=solarize:solarize requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY --chown=solarize:solarize . .

# Expose Daphne port
EXPOSE 8000

# Start Daphne
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "solarize.asgi:application"]

