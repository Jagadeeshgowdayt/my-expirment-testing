FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY broadcast_bot.py .

EXPOSE 8443
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost:8443/ || exit 1

CMD ["python", "broadcast_bot.py"]
