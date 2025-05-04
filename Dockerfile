FROM python:3.12-slim

WORKDIR /app

COPY requirements-rebel.txt /app/requirements.txt

RUN pip install -r requirements.txt --no-cache-dir

COPY src/ /app/src/
COPY pyproject.toml /app/pyproject.toml

RUN pip install .

COPY server.py /app/server.py

COPY init_rebel.py /app/init_rebel.py

RUN python init_rebel.py

EXPOSE 8000

CMD [ "fastapi", "run", "server.py" ]