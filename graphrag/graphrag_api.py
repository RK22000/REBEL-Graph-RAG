from typing import List, Dict, Any, Optional
import networkx as nx
import nx_arangodb as nxadb
from langchain_community.graphs import ArangoGraph
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain
from langchain_core.tools import tool
from graphrag_utils import *
import logging
logger = logging.getLogger(__name__)
from fastapi import HTTPException

from dotenv import load_dotenv

import requests
import json

load_dotenv()

db = ArangoClient(hosts=os.getenv("ARANGODB_URL")).db(username="root", password=os.getenv("ARANGODB_PASS"), verify=True)

@app.post("/query")
async def query_kb(input):
    """
    Query the knowledge base using natural language
    """
    try:
        result = query_graph(input.query)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error querying knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 


