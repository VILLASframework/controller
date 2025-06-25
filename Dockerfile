FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt

COPY . /tmp/controller

RUN cd /tmp/controller && \
    python3 setup.py sdist && \
    pip install dist/*.tar.gz && \
    rm -rf /tmp/controller

ENTRYPOINT ["villas-controller"]