# Base image: slim Python
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create non-root user early
RUN groupadd -r solarize && \
    useradd -r -g solarize -d /home/solarize -m solarize

# Pre-create staticfiles directory for mounting
RUN mkdir -p /solarize/staticfiles /solarize/media \
    && chown -R solarize:solarize /solarize/staticfiles /solarize/media

WORKDIR /solarize

# Switch to non-root user
USER solarize

# Install Python dependencies AS the non-root user
COPY --chown=solarize:solarize requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy the rest of the code
COPY --chown=solarize:solarize . .



# Make sure .local/bin is in PATH
ENV PATH="/home/solarize/.local/bin:${PATH}"

EXPOSE 8000
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "solarize.asgi:application"]
