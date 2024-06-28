FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

ENV PYTHONFAULTHANDLER=1 \
PYTHONUNBUFFERED=1 \
PYTHONHASHSEED=random \
PIP_NO_CACHE_DIR=off \
PIP_DISABLE_PIP_VERSION_CHECK=on \
PIP_DEFAULT_TIMEOUT=100 \
POETRY_NO_INTERACTION=1 \
POETRY_VIRTUALENVS_CREATE=false \
POETRY_CACHE_DIR='/var/cache/pypoetry' \
POETRY_HOME='/usr/local' \
POETRY_VERSION=1.8.2

RUN apt-get update && \
    apt-get install -y git curl python3-pip python3-dev python-is-python3 && \
    rm -rf /var/lib/apt/lists/*

# install PDM
RUN pip install -U pdm
# disable update check

ENV PDM_CHECK_UPDATE=false

WORKDIR /code
COPY pdm.lock pyproject.toml /code/

RUN pdm install --prod --project /code --check --global

COPY . /code
