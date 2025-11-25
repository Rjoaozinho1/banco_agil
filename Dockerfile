FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc

COPY requirements.txt ./
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /app/wheels /app/wheels
RUN pip install --no-cache /app/wheels/*

COPY . .
COPY data ./data

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]