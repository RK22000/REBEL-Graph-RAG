FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt --no-cache-dir

COPY src/ /app/src/
COPY pyproject.toml /app/pyproject.toml

RUN pip install .

COPY server.py /app/server.py

EXPOSE 8000

CMD [ "fastapi", "run", "server.py" ]