FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN mkdir -p /app/staticfiles /app/media \
    && touch /app/debug.log \
    && groupadd -r solarize \
    && useradd -r -g solarize -ms /bin/bash solarize \
    && chown -R solarize:solarize /app

USER solarize

RUN python3 manage.py collectstatic --no-input

EXPOSE 8000
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "solarize.asgi:application"]
