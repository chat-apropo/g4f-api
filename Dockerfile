FROM python:3.12.2-slim-bullseye

WORKDIR /backend
COPY backend/ backend
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "-m", "backend.run"]
