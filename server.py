from fastapi import FastAPI
from pydantic import BaseModel
from rebel.rebel import make_kb
from rebel.rebel import extract_knowledge_graph
import logging
import torch
logger = logging.getLogger(__name__)

class Corpus(BaseModel):
    chunks: list[str]
    
class StatusCheck(BaseModel):
    status: str
    cuda_available: bool

app = FastAPI()


@app.get('/healthy')
def health_check() -> StatusCheck:
    logger.info("Health check ok")
    return StatusCheck(status='OK', cuda_available=torch.cuda.is_available())
    # return {
    #     "status": 'OK',
    #     "cuda_available": torch.cuda.is_available()
    # }

@app.post('/kbv2')
def to_kb_v2(corpus: Corpus, span_length:int=128, batch_size:int=10, device:str='cpu', timeout:int=1) -> list[ list[list[str]] ]:
    knowledge_graphs = []
    for chunk in corpus.chunks:
        relation = extract_knowledge_graph(chunk, span_length, batch_size, torch.device(device), False, timeout)
        knowledge_graphs.append(relation)
    return knowledge_graphs


@app.post('/kb')
def to_kn(corpus: Corpus) -> list[list[str]]:
    kb = set()
    for chunk in corpus.chunks:
        kb.update(make_kb(chunk))
    return kb
