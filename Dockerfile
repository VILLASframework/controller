FROM python:3.11

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc python3-dev pkg-config && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip setuptools wheel build && \
    python -m build

RUN pip install --no-build-isolation --no-cache-dir dist/*.tar.gz

ENTRYPOINT ["villas-controller"]
