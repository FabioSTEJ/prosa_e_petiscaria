FROM python:3.12-slim

ENV TZ=America/Sao_Paulo
RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/
COPY run.py .
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh && mkdir -p /app/data

ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

VOLUME ["/app/data"]

EXPOSE 5500

CMD ["./entrypoint.sh"]
