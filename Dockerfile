# PDI as one container: the vault console built and served by the API.
#
# Two stages so the Node toolchain never ships in the runtime image — only the
# built console does. The result serves the UI at /app and the API on the same
# origin, which is what lets a phone use it with nothing to configure.
#
#   docker build -t pdi .
#   docker run -p 8100:8100 -v pdi-data:/data \
#     -e PDI_MASTER_KEY="$(openssl rand -base64 32)" \
#     -e PDI_ADMIN_TOKEN=... \
#     -e PDI_PUBLIC_URL=https://vault.example.com pdi
#
# **The master key is the vault.** Lose it and every sealed record is gone;
# leak it and the ciphertext is decorative. It is passed at runtime and never
# baked into the image. Read docs/hosting.md and the key-custody table in
# docs/operations.md before publishing one.
#
# The suite end-to-end harness (docker/docker-compose.yml in the qrme repo)
# builds this image, so changes here have to keep working there too.

# --- stage 1: build the console ------------------------------------------
FROM node:20-slim AS console
WORKDIR /src
# Copy manifests first so dependency install caches independently of source.
COPY app/package.json app/package-lock.json ./app/
RUN npm --prefix app ci
COPY app/ ./app/
RUN npm --prefix app run build

# --- stage 2: the service ------------------------------------------------
FROM python:3.12-slim AS runtime

# Predictable, unbuffered logs; no .pyc clutter in the layer.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PDI_DB=/data/pdi.db \
    PDI_CONSOLE_DIR=/srv/app/dist

WORKDIR /srv
COPY pyproject.toml README.md ./
COPY pdi/ ./pdi/
RUN pip install --no-cache-dir .

# The built console, mounted by the API at /app. PDI_CONSOLE_DIR points at it
# explicitly: the installed package lives in site-packages, so the relative
# path the source tree uses would not find this copy.
COPY --from=console /src/app/dist ./app/dist

# The vault lives on a volume, not in the image. This one is not merely
# "don't lose data" — sealed records that outlive their database are
# unrecoverable, and the audit chain that proves who read what lives here too.
RUN useradd --system --uid 10001 pdi \
 && mkdir -p /data && chown -R pdi:pdi /data /srv
USER pdi
VOLUME ["/data"]

EXPOSE 8100
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8100/health').status==200 else 1)"

# PORT is honoured for platforms that assign one (Fly, Render, Railway…).
CMD ["sh", "-c", "uvicorn pdi.api:app --host 0.0.0.0 --port ${PORT:-8100}"]
