# Solarize Dockerfile

FROM python:3.12-slim

# Avoid interactive prompts & buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create non-root user early
ARG APP_USER=solarize
ARG APP_UID=1000
ARG APP_GID=1000

RUN groupadd --gid $APP_GID $APP_USER && \
    useradd --uid $APP_UID --gid $APP_GID --create-home --shell /bin/bash $APP_USER && \
    mkdir -p /app/staticfiles /app/media && \
    chown $APP_USER:$APP_USER /app/staticfiles /app/media

WORKDIR /app

# Switch to non-root user BEFORE installing packages
USER $APP_USER

# Install Python dependencies into user-local (so they survive read-only root)
COPY --chown=$APP_USER:$APP_USER requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Ensure user-local bin directory is on PATH
ENV PATH="/home/$APP_USER/.local/bin:${PATH}"

# Copy application code (read-only in production)
COPY --chown=$APP_USER:$APP_USER . .

# Expose Daphne port
EXPOSE 8000

# Run Daphne (Channels ASGI server)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "solarize.asgi:application"]