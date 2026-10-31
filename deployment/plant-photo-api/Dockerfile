FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 YOLO_CONFIG_DIR=/tmp/ultralytics PLANT_MODEL_PATH=/app/models/plant_disease_best.pt INFERENCE_DEVICE=cpu
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-doctor.txt ./
RUN pip install --no-cache-dir torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir -r requirements-doctor.txt gunicorn==23.0.0
COPY ai-backend/ ./ai-backend/
COPY models/ ./models/
RUN useradd --uid 10001 --create-home appuser
USER appuser
EXPOSE 8008
WORKDIR /app/ai-backend
CMD ["gunicorn", "--bind", "0.0.0.0:8008", "--workers", "1", "--threads", "2", "--timeout", "60", "plant_api:create_app()"]
