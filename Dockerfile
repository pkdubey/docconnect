FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Build arg: set to "true" when USE_POSTGIS=true to install GDAL/GEOS system libs
ARG USE_POSTGIS=false

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && if [ "$USE_POSTGIS" = "true" ]; then \
         apt-get install -y gdal-bin libgdal-dev libgeos-dev; \
       fi \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
