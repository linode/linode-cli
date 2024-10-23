FROM python:3.11-slim AS builder

ARG linode_cli_version

WORKDIR /src

RUN apt-get update && \
    apt-get install -y make git

COPY . .

RUN make requirements

RUN LINODE_CLI_VERSION=$linode_cli_version make build

FROM python:3.11-slim

COPY --from=builder /src/dist /dist

RUN pip3 install /dist/*.whl boto3

RUN useradd -ms /bin/bash cli
USER cli:cli

ENTRYPOINT ["linode-cli"]
