FROM python:3.10

WORKDIR /app

COPY requirements.txt /app/
COPY yugisearcher/ /app/

# Install psycopg2 deps
RUN apt-get update \
    && apt-get install -y libpq-dev python3-dev build-essential wget \
    && wget https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-v0.6.1.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-v0.6.1.tar.gz \
    && rm dockerize-linux-amd64-v0.6.1.tar.gz \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

ENV DJANGO_SETTINGS_MODULE=yugisearcher.settings

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
