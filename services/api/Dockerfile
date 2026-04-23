FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Strip any CRLF line endings that may have been introduced by a Windows
# checkout (core.autocrlf=true) and ensure the script is executable. Then
# invoke via /bin/sh so we do not depend on the x-bit surviving a bind mount.
RUN sed -i 's/\r$//' /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

CMD ["/bin/sh", "/app/entrypoint.sh"]