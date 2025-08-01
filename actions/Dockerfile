FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 5055

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "5055"]
