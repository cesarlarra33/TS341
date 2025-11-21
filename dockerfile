

FROM python:3.11-slim
WORKDIR /app
# Installer les dépendances système nécessaires à OpenCV et Streamlit
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# Installer poetry
RUN pip install --no-cache-dir poetry

# Copier les fichiers nécessaires
COPY pyproject.toml poetry.lock* README.md ./
COPY ts341_project ./ts341_project
COPY app.py ./

# Installer les dépendances Python
RUN poetry install --no-interaction --no-ansi

EXPOSE 8501
CMD ["poetry", "run", "streamlit", "run", "app.py", "--server.address=0.0.0.0"]
