FROM python:3.11

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && \
    pip install -m build

COPY . /tmp/controller

RUN cd /tmp/controller && \
    python3 setup.py sdist && \
    pip install dist/*.tar.gz && \
    rm -rf /tmp/controller

ENTRYPOINT ["villas-controller"]