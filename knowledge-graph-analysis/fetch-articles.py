import os
from hashlib import sha1
import wikipedia
from tqdm import tqdm
import pandas as pd

list_file = "data/wikipedia-top-25.txt"
article_dir = "data/articles"
table_file = "data/article-table.csv"

os.makedirs(article_dir, exist_ok=True)

with open(list_file, "r") as f:
    articles = list(map(lambda i: i.strip(), f.readlines()))

# print(articles)
# hashes = [ str(abs(hash(i))) for i in articles ]
hashes = [sha1(i.encode()).hexdigest() for i in articles]
# print(hashes)

def download_article(article, hash_id):
    page = wikipedia.page(article)
    with open(f"{article_dir}/{hash_id}.txt", 'w') as f:
        f.write(page.content)


table = []
for article, hash_id in tqdm(zip(articles, hashes), total=len(articles)):
    try:
        download_article(article, hash_id)
        table.append(( hash_id, article ))
        # print(f"Downloaded: {article}")
    except:
        # print(f"Error on {article}")
        pass

pd.DataFrame(table, columns=["hash_id", "article"]).to_csv(table_file, index=None)