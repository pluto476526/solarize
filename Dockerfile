FROM python:3.12-slim

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# Copy requirements early to use Docker cache
COPY requirements.txt /app/

# Copy the rest of the project
COPY . /app/

# Create directories that Django needs
RUN touch /app/debug.log \
    && mkdir -p /app/static \
    && mkdir -p /app/media \
    && groupadd -r solarize \
    && useradd -r -g solarize -ms /bin/bash solarize \
    && chown -R solarize:solarize /app \
    && pip install --no-cache-dir -r requirements.txt


# Switch to the non-root user
USER solarize

# Expose port
EXPOSE 8000

# Default command
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "solarize.asgi:application"]
