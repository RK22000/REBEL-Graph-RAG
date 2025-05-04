import torch
import pandas as pd
from rebel.rebel import extract_knowledge_graph
from tqdm import tqdm
import os

table_file = "data/article-table.csv"
article_dir = "data/articles"
kg_dir = 'data/knowledge-graphs'

os.makedirs(kg_dir, exist_ok=True)


device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
print(f'Using: {device}')

article_df = pd.read_csv(table_file)

def extract_and_save_knowledge_graph(text_file, hash_id):
    with open(text_file, 'r') as f:
        txt = f.read()

    kb = extract_knowledge_graph(
        text=txt,
        span_length=128,
        batch_size=5,
        device=device,
        prog_bar=False,
        timeout_minutes=5,
        silent=True
    )
    kb_table = pd.DataFrame(kb, columns=['head', 'relation', 'tail'])
    kb_table.to_csv(f"{kg_dir}/{hash_id}.csv", index=None)
    return kb_table

for hash_id in tqdm(article_df.hash_id):
    try:
        t = extract_and_save_knowledge_graph(f"{article_dir}/{hash_id}.txt", hash_id)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(e)
        pass

