from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from langchain_deepseek import ChatDeepSeek
from arango import ArangoClient
import os
from dotenv import load_dotenv
import requests
import json
import re
import networkx as nx
import nx_arangodb as nxadb
from langchain_community.graphs import ArangoGraph
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain
from langgraph.prebuilt import create_react_agent

from properties import (
    ARANGO_URL, ARANGO_DB, ARANGO_USER, ARANGO_PASSWORD,
    DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_TEMPERATURE,
    REBEL_API_URL
)

logger = logging.getLogger(__name__)
app = FastAPI(title="GraphRAG API")
db = ArangoClient(hosts=ARANGO_URL).db(username=ARANGO_USER, password=ARANGO_PASSWORD, verify=True)
llm = ChatDeepSeek(
    temperature=DEEPSEEK_TEMPERATURE,
    model_name=DEEPSEEK_MODEL,
    api_key=DEEPSEEK_API_KEY
)
arango_graph = ArangoGraph(db)
class TextInput(BaseModel):
    text: str
class QueryInput(BaseModel):
    query: str

def chunkify(text, chunk_size=500, overlap=50 ):
    text = re.sub(r'\s+', ' ', text.strip())
    sentences = re.split('(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_length = 0
    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length > chunk_size and current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
            overlap_size = 0
            overlap_sentences = []
            for s in reversed(current_chunk):
                if overlap_size + len(s) > overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_size += len(s) + 1 
            current_chunk = overlap_sentences
            current_length = overlap_size
        current_chunk.append(sentence)
        current_length += sentence_length + 1 
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

def rebel_api_call(chunks):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'chunks': chunks
    }
    
    try:
        response = requests.post(REBEL_API_URL, headers=headers, json=payload)
        response.raise_for_status()  
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def text2kb(input_text: str) -> Dict[str, Any]:
    """Convert text to knowledge base using REBEL"""
    chunks = chunkify(input_text)
    result = rebel_api_call(chunks)
    return result

def text_to_aql_to_text(arango_graph, query: str):
    """
    
    Args:
        query: any query
    Returns:
        None
    """
    chain = ArangoGraphQAChain.from_llm(
    	llm=llm,
    	graph=arango_graph,
    	verbose=True,
        allow_dangerous_requests=True
    )

    result = chain.invoke(query)

    return str(result["result"])

def text_to_nx_algorithm_to_text(arango_graph, query):
    """
    
    Args:
        query: any query
    Returns:
        None
    """
    print("1) Generating NetworkX code")

    text_to_nx = llm.invoke(f"""
    I have a NetworkX Graph called `G_adb`. It has the following schema: {arango_graph.schema}
    I have the following graph analysis query: {query}.
    Generate the Python Code required to answer the query using the `G_adb` object.
    Be very precise on the NetworkX algorithm you select to answer this query. Think step by step.
    Only assume that networkx is installed, and other base python dependencies.
    Always set the last variable as `FINAL_RESULT`, which represents the answer to the original query.
    Only provide python code that I can directly execute via `exec()`. Do not provide any instructions.
    Make sure that `FINAL_RESULT` stores a short & consice answer. Avoid setting this variable to a long sequence.

    Your code:
    """).content

    text_to_nx_cleaned = re.sub(r"^```python\n|```$", "", text_to_nx, flags=re.MULTILINE).strip()

    print('-'*10)
    print(text_to_nx_cleaned)
    print('-'*10)
    
    print("\n2) Executing NetworkX code")
    global_vars = {"G_adb": G_adb, "nx": nx}
    local_vars = {}

    try:
        exec(text_to_nx_cleaned, global_vars, local_vars)
        text_to_nx_final = text_to_nx
    except Exception as e:
        print(f"EXEC ERROR: {e}")
        return f"EXEC ERROR: {e}"

        # TODO: need a code correction mechanism
        # TODO: add attempt limit?
    print('-'*10)
    FINAL_RESULT = local_vars["FINAL_RESULT"]
    print(f"FINAL_RESULT: {FINAL_RESULT}")
    print('-'*10)

    print("3) Formulating final answer")

    nx_to_text = llm.invoke(f"""
        I have a NetworkX Graph called `G_adb`. It has the following schema: {arango_graph.schema}
        I have the following graph analysis query: {query}.
        I have executed the following python code to help me answer my query:

        ---
        {text_to_nx_final}
        ---

        The `FINAL_RESULT` variable is set to the following: {FINAL_RESULT}.
        Based on my original Query and FINAL_RESULT, generate a short and concise response to
        answer my query.

        Your response:
    """).content

    return nx_to_text

tools = [text_to_aql_to_text, text_to_nx_algorithm_to_text]

def query_graph(query):
    app = create_react_agent(llm, tools)
    final_state = app.invoke({"messages": [{"role": "user", "content": query}]})
    return final_state["messages"][-1].content