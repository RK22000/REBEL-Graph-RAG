Install dependencies in your venv
```
pip install -Ur requirements.txt
```
run the server (dev mode, auto reloads on file change)
```
fastapi dev server.py
```

To run the graphRAG application:
1. Set up a `.env` file with the following variables:
ADBPASS (ArangoDB password)
DEEPSEEK_API_KEY (DeepSeek API password)

2. run `python graphrag_api.py`

3. cURL command for /query:
```bash
curl -X POST \
  http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What is the relationship between Node2Vec and random walks?"
  }'
```