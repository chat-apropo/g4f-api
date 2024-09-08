FROM python:3.12.2-slim-bullseye
RUN apt-get update && apt-get install -y curl gcc python3-dev
WORKDIR /backend
COPY backend/ backend
COPY static/ static
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "-m", "backend.run"]
