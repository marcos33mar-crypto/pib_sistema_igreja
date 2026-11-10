FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt || true

EXPOSE 8090
ENV PORT=8090

CMD ["python", "server.py"]
