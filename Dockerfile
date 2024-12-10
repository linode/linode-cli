FROM python:3.12-slim AS builder

ARG linode_cli_version

ARG github_token

WORKDIR /src

RUN apt-get update && \
    apt-get install -y --no-install-recommends make git && \
    rm -rf /var/lib/apt/lists/*

COPY . .

RUN make requirements

RUN LINODE_CLI_VERSION=$linode_cli_version GITHUB_TOKEN=$github_token make build

FROM python:3.12-slim

COPY --from=builder /src/dist /dist

RUN pip3 install --no-cache-dir /dist/*.whl boto3

RUN useradd -ms /bin/bash cli
USER cli:cli

ENTRYPOINT ["linode-cli"]
