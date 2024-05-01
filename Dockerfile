FROM python:3.12.2-slim-bullseye
RUN apk add --no-cache curl # fix healthcheck

WORKDIR /backend
COPY backend/ backend
COPY static/ static
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "-m", "backend.run"]
