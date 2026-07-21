# PDI backend image — `uvicorn pdi.api:app`. Needs a master key at runtime
# (PDI_MASTER_KEY, base64 of 32 bytes) or a configured KMS provider.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md ./
COPY pdi ./pdi
RUN pip install .

EXPOSE 8100
CMD ["uvicorn", "pdi.api:app", "--host", "0.0.0.0", "--port", "8100"]
