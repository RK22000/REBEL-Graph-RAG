from typing import List, Dict, Any, Optional
import networkx as nx
import nx_arangodb as nxadb
from langchain_community.graphs import ArangoGraph
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain
from langchain_core.tools import tool
from graphrag_utils import *
import logging
logger = logging.getLogger(__name__)
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from arango import ArangoClient
import os
from dotenv import load_dotenv
import requests
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GraphRAG API", description="API for querying knowledge graphs")

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://rebel-graph-rag-1.onrender.com"],  # React development server and production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
db = ArangoClient(hosts=ARANGO_URL).db(username=ARANGO_USER, password=ARANGO_PASS, verify=True)

class QueryRequest(BaseModel):
    query: str

# Define API routes before mounting static files
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "message": "GraphRAG API is running"}

@app.post("/query")
async def query_kb(request: QueryRequest):
    """
    Query the knowledge base using natural language
    """
    try:
        print("Querying knowledge base...")
        result = query_graph(request.query)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error querying knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files last
app.mount("/", StaticFiles(directory="../UI/dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 


