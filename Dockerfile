FROM fedora:30

ENV PYCURL_SSL_LIBRARY openssl

RUN dnf -y install \
	gcc \
	curl \
	python3 \
	python3-pip \
	python3-devel \
	libcurl-devel \
	openssl-devel \
	nmap-ncat

COPY . /tmp/controller
RUN cd /tmp/controller && \
    python3 setup.py install && \
    rm -rf /tmp/controller

ADD https://raw.githubusercontent.com/eficode/wait-for/master/wait-for /usr/bin/wait-for
RUN chmod +x /usr/bin/wait-for

