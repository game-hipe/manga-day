FROM python:3.14.2-slim-bookworm

WORKDIR /app

RUN mkdir /app/var

VOLUME [ "/app/var" ]

COPY requirements.txt .

RUN pip isntall -r requirements.txt --no-cache-dir

COPY . .

CMD [ "python", "main.py" ]