# build stage
FROM python:3.11 AS builder

WORKDIR /build
COPY . .

RUN pip install .

RUN python3 setup.py sdist && \
    pip install dist/*.tar.gz --target /install

# minimal runtime image
FROM python:3.11-slim AS runtime

COPY --from=builder /install /usr/local/lib/python3.11/site-packages
COPY etc/*.json etc/*.yaml /etc/villas/controller/
COPY villas-controller.service /etc/systemd/system/

ENTRYPOINT ["/usr/local/lib/python3.11/site-packages/bin/villas-controller"]
