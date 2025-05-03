#!/bin/bash
set -e

cd UI
npm install --include=dev
npm run build
cd ..

pip install -r requirements.txt

mkdir -p static
cp -r UI/dist/* static/

cd graphrag

uvicorn graphrag_api:app --host 0.0.0.0 --port 8000