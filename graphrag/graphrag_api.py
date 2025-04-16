from typing import List, Dict, Any, Optional
import networkx as nx
import nx_arangodb as nxadb
from langchain_community.graphs import ArangoGraph
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain

from graphrag_utils import *

@app.post("/text-to-kb")
async def text_to_kb(input: TextInput) -> Dict[str, Any]:
    """
    Convert text input to knowledge base using REBEL and store in ArangoDB
    """
    try:
        edge_list = text2kb(input.text)
        G = nx.DiGraph()

        for node1, relation, node2 in edge_list:
            G.add_edge(node1, node2, relationship=relation)

        G_adb = nxadb.Graph(
            name=input.db_name,
            db=db,
            incoming_graph_data=G,
            write_batch_size=50000 
        )
        return {"message": "Knowledge base created successfully", "data": edge_list}
    except Exception as e:
        logger.error(f"Error creating knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_kb(input: QueryInput) -> Dict[str, str]:
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
    uvicorn.run(app, host="0.0.0.0", port=8000) 