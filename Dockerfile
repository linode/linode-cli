FROM python:3.11-slim AS builder

ARG linode_cli_version
ARG github_token

WORKDIR /src

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y make git && \
    pip3 install -r requirements.txt && \
    pip3 install build

COPY . .

RUN LINODE_CLI_VERSION=$linode_cli_version GITHUB_TOKEN=$github_token make build

FROM python:3.11-slim

COPY --from=builder /src/dist /dist

RUN pip3 install /dist/*.whl boto3

RUN useradd -ms /bin/bash cli
USER cli:cli

ENTRYPOINT ["linode-cli"]
