# Gunakan base image Python yang ringan
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Jakarta

# Set working directory di dalam container
WORKDIR /app

# Salin requirements.txt dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi ke dalam container
COPY . .

# Jalankan bot
CMD ["python", "-m", "bot.main"]
