FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install shared package
COPY ../../shared /shared
RUN pip install -e /shared

CMD ["python", "main.py"]