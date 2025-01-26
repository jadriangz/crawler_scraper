FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    fonts-freefont-ttf \
    xvfb \
    libxcb1 \
    libxrandr2 \
    libxv1 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*
RUN pip install playwright && playwright install chromium
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "src/main.py"]