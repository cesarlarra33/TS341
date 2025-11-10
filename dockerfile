
FROM python:3.11-slim AS builder
WORKDIR /app
# Installer les dépendances système nécessaires à OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* README.md ./
RUN pip install poetry
COPY ts341_project ./ts341_project
RUN poetry build -f wheel


FROM python:3.11-slim
WORKDIR /app
# Installer à nouveau les libs système requises (pas héritées du builder)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/dist/*.whl ./
RUN pip install *.whl
COPY ts341_project ./ts341_project

EXPOSE 5000
CMD ["python", "ts341_project/main.py"]
