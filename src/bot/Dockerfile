FROM python:3.14.2-slim-bookworm

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD [ "python", "main.py" ]