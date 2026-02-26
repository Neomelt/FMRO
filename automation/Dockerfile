FROM python:3.11-slim

# Use mirror sources for faster downloads in China
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true

RUN apt-get update && apt-get install -y --no-install-recommends \
    android-tools-adb \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    libtesseract-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# Playwright: use Chinese CDN mirror
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
RUN playwright install --with-deps chromium
RUN scrapling install

COPY . .

CMD ["python", "-m", "pytest", "tests/test_smoke.py", "-v"]
