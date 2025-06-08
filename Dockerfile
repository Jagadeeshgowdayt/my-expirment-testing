# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY simple_bot.py .

# Expose dummy port for Koyeb health check
EXPOSE 8443

# Health check to ensure bot process is alive
HEALTHCHECK --interval=30s --timeout=5s \
  CMD pgrep -f simple_bot.py >/dev/null || exit 1

# Start the bot
CMD ["python", "simple_bot.py"]
