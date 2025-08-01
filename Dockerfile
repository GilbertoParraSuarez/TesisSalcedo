FROM python:3.9-slim

WORKDIR /app

# Instala dependencias del sistema para Debian
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev libffi-dev libssl-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5055
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5055"]