FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY simple_bot.py .

# EXPOSE the same port your HTTP server uses
EXPOSE 8443

# (Optional) keep the pgrep-based healthcheck too
HEALTHCHECK --interval=30s --timeout=5s \
  CMD pgrep -f simple_bot.py >/dev/null || exit 1

CMD ["python", "simple_bot.py"]
