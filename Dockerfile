# Use an official lightweight Python image.
FROM python:3.11-slim

# Set working directory.
WORKDIR /app

# Copy requirements and install.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code.
COPY simple_bot.py .

# Tell Koyeb to run this.
CMD ["python", "simple_bot.py"]
