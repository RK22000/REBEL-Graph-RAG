from fastapi import FastAPI
from pydantic import BaseModel
from rebel.rebel import make_kb
import logging
logger = logging.getLogger(__name__)

class Corpus(BaseModel):
    chunks: list[str]

app = FastAPI()

@app.get('/healthy')
def health_check():
    logger.info("Health check ok")
    return 'OK'


@app.post('/kb')
def to_kn(corpus: Corpus) -> list[list[str]]:
    kb = set()
    for chunk in corpus.chunks:
        kb.update(make_kb(chunk))
    return kb
