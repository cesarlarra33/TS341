
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry
COPY ts341_project ./ts341_project
RUN poetry build -f wheel

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app/dist/*.whl ./
RUN pip install *.whl
COPY ts341_project ./ts341_project
EXPOSE 5000
CMD ["python", "ts341_project/main.py"]
