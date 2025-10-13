FROM python:3.11-slim 

RUN pip install poetry

WORKDIR /app
COPY . /app

RUN poetry install

EXPOSE 5000 
CMD ["poetry", "run", "python", "ts341_example/app.py"]