import pandas as pd
from tqdm import tqdm

def measure_symetry(knowledge_graph, relation):
    # relation = "twinned administrative body"
    kb_subset = knowledge_graph.loc[knowledge_graph['relation']==relation]
    tails, heads = kb_subset['tail'], kb_subset['head']
    count = 0
    for head, tail in zip(heads, tails):
        if len(kb_subset.loc[(heads==tail) & (tails==head)]) > 0:
            count += 1
    score = count / len(kb_subset)
    return score
def measure_anti_symetry(knowledge_graph, relation):
    kb_subset = knowledge_graph.loc[knowledge_graph['relation']==relation]
    tails, heads = kb_subset['tail'], kb_subset['head']
    count = 0
    for head, tail in zip(heads, tails):
        if len(kb_subset.loc[(heads==tail) & (tails==head)]) == 0:
            count += 1
    score = count / len(kb_subset)
    return score
    
def find_inverse(knowledge_graph, relation) -> dict[str, float]:
    # relation = "product or material produced"
    relations = knowledge_graph['relation'].unique()
    inv_score = pd.Series(0, index=relations)
    kb_subset = knowledge_graph.loc[knowledge_graph['relation']==relation]

    for i, (head, tail) in kb_subset[['head', 'tail']].iterrows():
        inverses = knowledge_graph.loc[(knowledge_graph['head']==tail) & (knowledge_graph['tail']==head)]['relation']
        inv_score[inverses]+=1
    inv_score /= len(kb_subset)
    return inv_score

def measure_inverse(knowledge_graph, relation):
    return sum(find_inverse(knowledge_graph, relation))

def measure_composite(knowledge_graph, relation, composite_matrix=None):
    # relation = 'part of'
    kb_subset = knowledge_graph.loc[knowledge_graph['relation']==relation]
    if composite_matrix is None:
        entities = pd.concat([knowledge_graph['head'], knowledge_graph['tail']]).unique()
        adj_mat = pd.DataFrame(0, entities, entities)
        for i, (head, tail) in knowledge_graph[['head', 'tail']].iterrows():
            adj_mat.loc[head, tail] += 1
        composite_matrix = ((adj_mat @ adj_mat) * (adj_mat>0))
        measure_composite.composite_matrix = composite_matrix
    score = 0
    for i, (head, _, tail) in kb_subset.iterrows():
        score += composite_matrix.loc[head, tail]
    score /= len(kb_subset)
    return score

def measure_one_many(knowledge_graph, relation):
    # relation = 'has part'
    kb_subset = knowledge_graph.loc[knowledge_graph['relation']==relation]
    return len(kb_subset) / len(kb_subset['head'].unique())

def count(knowledge_graph, relation):
    kb_subset = knowledge_graph.loc[knowledge_graph['relation']==relation]
    return len(kb_subset)
    

table_file = "data/article-table.csv"
relation_score_file = "data/relation-scores.csv"


article_table = pd.read_csv(table_file, )
kg_dir = 'data/knowledge-graphs'

knowledge_graphs = [ pd.read_csv(f"{kg_dir}/{hash_id}.csv").drop_duplicates() for hash_id in article_table['hash_id']]

unified_graph = pd.concat(knowledge_graphs).drop_duplicates()

relations = unified_graph['relation'].unique()

measure_composite(unified_graph, relations[0]) # initialize cached composite matrix
metric_method_pairs = [
    ("symetry score", measure_symetry),
    ("anti symetry score", measure_anti_symetry),
    ("inverse score", measure_inverse),
    ("composite score", lambda knowledge_graphs, relation: measure_composite(knowledge_graphs, relation, measure_composite.composite_matrix)),
    ("one many score", measure_one_many),
    ("count", count)
]
score = {}


for relation in tqdm(relations):
    for metric, method in metric_method_pairs:
        score.setdefault(metric, []).append(method(unified_graph, relation))

score_table = pd.DataFrame(score, index=pd.Index(relations, name='Relations'))
score_table.to_csv(relation_score_file)
    


