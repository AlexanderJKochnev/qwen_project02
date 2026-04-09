FROM python:3.12-slim AS builder
RUN apt update && apt install -y git cmake build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim
RUN apt update && apt install -y libgomp1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
CMD ["python", "main.py"]