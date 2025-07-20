FROM python:3.11-slim

WORKDIR /app

# ① system deps + build tools + python deps in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc portaudio19-dev libasound-dev libsndfile1-dev \
   && pip install --no-cache-dir pip wheel \
   && rm -rf /var/lib/apt/lists/*

# ② copy & install python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ③ copy app code, set user etc. (unchanged)
COPY . .
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
