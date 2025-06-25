FROM python:3.11

RUN pip install --upgrade pip setuptools wheel build && \
    python -m build

COPY . /tmp/controller

RUN cd /tmp/controller && \
    python3 setup.py sdist && \
    pip install dist/*.tar.gz && \
    rm -rf /tmp/controller

ENTRYPOINT ["villas-controller"]