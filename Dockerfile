# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY broadcast_bot.py .

# Expose port for health check
EXPOSE 8443

# Container-level health check (fallback)
HEALTHCHECK --interval=30s --timeout=5s \
  CMD pgrep -f broadcast_bot.py >/dev/null || exit 1

# Start the bot
CMD ["python", "broadcast_bot.py"]
