# build stage
FROM python:3.11 AS builder

WORKDIR /build
COPY . .

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc python3-dev pkg-config && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip setuptools wheel build

RUN python -m build && \
    pip install dist/*.tar.gz --prefix=/install

# runtime stage
FROM python:3.11-slim AS runtime

# copy installed Python libs + CLI scripts
COPY --from=builder /install /usr/local

COPY etc/*.json etc/*.yaml /etc/villas/controller/
COPY villas-controller.service /etc/systemd/system/

ENTRYPOINT ["villas-controller"]
