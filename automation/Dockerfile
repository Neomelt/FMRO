FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    android-tools-adb \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    libtesseract-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install --with-deps chromium
RUN scrapling install

COPY . .

CMD ["python", "-m", "pytest", "tests/test_smoke.py", "-v"]
