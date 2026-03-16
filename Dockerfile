FROM python:3.14.2-slim-bookworm

WORKDIR /app

RUN mkdir /app/var
RUN mkdir /app/var/pdf

VOLUME [ "/app/var" ]

COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]