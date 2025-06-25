# build stage
FROM python:3.11 AS builder

WORKDIR /build
COPY . .

RUN pip install build
RUN python3 -m build

#RUN python3 setup.py sdist && \
#    pip install dist/*.tar.gz --target /install

# minimal runtime image
FROM python:3.11-slim AS runtime

COPY --from=builder /build/dist/*.tar.gz /tmp/
RUN pip install /tmp/*.tar.gz

COPY etc/*.json etc/*.yaml /etc/villas/controller/
COPY villas-controller.service /etc/systemd/system/

ENTRYPOINT ["villas-controller"]