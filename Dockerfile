# syntax=docker/dockerfile:1

FROM node:22-alpine AS ui-builder

WORKDIR /ui

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html vite.config.ts tsconfig.json ./
COPY src ./src

ARG VITE_WS_URL=ws://localhost:8765
ENV VITE_WS_URL=$VITE_WS_URL

RUN npm run build

FROM python:3.12-slim-bookworm AS python-base

ARG GITLEAKS_VERSION=8.24.2
ARG OSV_VERSION=1.9.2

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/* \
    && ARCH="$(dpkg --print-architecture)" \
    && case "$ARCH" in \
        amd64) GITLEAKS_ARCH=linux_x64; OSV_ARCH=linux_amd64 ;; \
        arm64) GITLEAKS_ARCH=linux_arm64; OSV_ARCH=linux_arm64 ;; \
        *) echo "unsupported architecture: $ARCH" >&2; exit 1 ;; \
    esac \
    && curl -fsSL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_${GITLEAKS_ARCH}.tar.gz" \
        | tar -xz -C /usr/local/bin gitleaks \
    && curl -fsSL "https://github.com/google/osv-scanner/releases/download/v${OSV_VERSION}/osv-scanner_${OSV_ARCH}" \
        -o /usr/local/bin/osv-scanner \
    && chmod +x /usr/local/bin/osv-scanner

WORKDIR /app

COPY pyproject.toml README.md ./
COPY spectre ./spectre
RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1 \
    WS_HOST=0.0.0.0 \
    SPECTRE_DATA_DIR=/app/data/sessions \
    SCOPE_DIR=/app/scopes

FROM python-base AS cli

ENTRYPOINT ["python", "-m", "spectre.cli"]

FROM python-base AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ui-builder /ui/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh

EXPOSE 8080 8765

ENTRYPOINT ["/app/docker/entrypoint.sh"]
