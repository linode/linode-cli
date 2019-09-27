FROM python:2-slim

ENV PYTHONPATH=.
ENV PATH="/usr/local/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/root/.local/bin"

RUN apt-get update && apt-get install -y git python3 python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

WORKDIR /src

COPY requirements.txt .

RUN pip install -r requirements.txt \
    && pip3 install -r requirements.txt \
    && pip install twine

COPY . .

# Build and Install the Linode CLI
ENTRYPOINT ["make", "build"]
