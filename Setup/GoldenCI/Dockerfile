FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Good to have for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget ca-certificates net-tools iproute2 iputils-ping dnsutils \
 && rm -rf /var/lib/apt/lists/*
