FROM python:3.11-slim

WORKDIR /app

ENV AI_PROVIDER=openai
ENV OPENAI_MODEL=gpt-5.4-mini
ENV GEMINI_MODEL=gemini-2.5-flash

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python train_models_kaggle.py --dataset ./data/intent_seed_dataset.csv

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
