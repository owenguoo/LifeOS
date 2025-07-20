FROM python:3.11-slim

WORKDIR /app

# ---- 1. system & build deps in ONE layer ----
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc g++ \
      portaudio19-dev libasound2 \
      libglib2.0-0 libsm6 libxext6 libxrender1 libgl1-mesa-glx \
      libgomp1 libjpeg-dev libpng-dev libtiff-dev \
      curl && \
    rm -rf /var/lib/apt/lists/*

# ---- 2. Python wheels ----
COPY requirements-web.txt .
RUN pip install --no-cache-dir --upgrade pip wheel \
 && pip install --no-cache-dir -r requirements-web.txt

# ---- 3. app code ----
COPY . .

# ---- 4. non‑root user ----
RUN useradd --create-home --shell /bin/bash app \
 && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "app.web_app:app", "--host", "0.0.0.0", "--port", "8000"]
