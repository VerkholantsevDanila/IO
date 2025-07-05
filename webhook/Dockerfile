FROM python:3.11-slim

WORKDIR /app
COPY webhook.py . 
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8088", "webhook:app"]
