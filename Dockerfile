# Build stage
FROM python:3.13 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc python3-dev pkg-config && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade \
    pip \
    setuptools \
    wheel \
    build

WORKDIR /build
COPY . .

RUN python -m build && \
    pip install dist/*.tar.gz --prefix=/install

# Runtime stage
FROM python:3.13-slim AS runtime

# Copy installed Python libs + CLI scripts
COPY --from=builder /install /usr/local

COPY etc/*.json etc/*.yaml /etc/villas/controller/
COPY villas-controller.service /etc/systemd/system/

ENTRYPOINT ["villas-controller"]
