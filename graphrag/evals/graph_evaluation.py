from typing import List, Set, Dict, Tuple
import numpy as np
from collections import defaultdict
import json
from graphrag_utils import text_to_aql_to_text
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

class GraphEvaluator:
    def __init__(self):
        self.metrics = {}
        # Initialize smoothing function for BLEU score
        self.smoothing = SmoothingFunction().method1

    def _get_triplets(self, subgraph: List[Dict]) -> Set[Tuple]:
        """Convert subgraph into set of triplets (head, relation, tail)"""
        triplets = set()
        for edge in subgraph:
            triplets.add((edge['head'], edge['relation'], edge['tail']))
        return triplets

    def precision_at_k(self, retrieved: List[Dict], gold: List[Dict], k: int) -> float:
        """
        Calculate precision@k for graph retrieval
        Args:
            retrieved: List of retrieved edges from AQL query
            gold: List of ground truth edges
            k: Number of top results to consider
        """
        retrieved_triplets = self._get_triplets(retrieved[:k])
        gold_triplets = self._get_triplets(gold)
        
        if not retrieved_triplets:
            return 0.0
            
        relevant_retrieved = retrieved_triplets.intersection(gold_triplets)
        return len(relevant_retrieved) / len(retrieved_triplets)

    def recall_at_k(self, retrieved: List[Dict], gold: List[Dict], k: int) -> float:
        """
        Calculate recall@k for graph retrieval
        Args:
            retrieved: List of retrieved edges from AQL query
            gold: List of ground truth edges
            k: Number of top results to consider
        """
        retrieved_triplets = self._get_triplets(retrieved[:k])
        gold_triplets = self._get_triplets(gold)
        
        if not gold_triplets:
            return 0.0
            
        relevant_retrieved = retrieved_triplets.intersection(gold_triplets)
        return len(relevant_retrieved) / len(gold_triplets)

    def f1_at_k(self, retrieved: List[Dict], gold: List[Dict], k: int) -> float:
        """
        Calculate F1@k for graph retrieval
        Args:
            retrieved: List of retrieved edges from AQL query
            gold: List of ground truth edges
            k: Number of top results to consider
        """
        precision = self.precision_at_k(retrieved, gold, k)
        recall = self.recall_at_k(retrieved, gold, k)
        
        if precision + recall == 0:
            return 0.0
            
        return 2 * (precision * recall) / (precision + recall)

    def jaccard_similarity(self, retrieved: List[Dict], gold: List[Dict]) -> float:
        """
        Calculate Jaccard similarity between retrieved and gold subgraphs
        Args:
            retrieved: List of retrieved edges from AQL query
            gold: List of ground truth edges
        """
        retrieved_triplets = self._get_triplets(retrieved)
        gold_triplets = self._get_triplets(gold)
        
        if not retrieved_triplets or not gold_triplets:
            return 0.0
            
        intersection = len(retrieved_triplets.intersection(gold_triplets))
        union = len(retrieved_triplets.union(gold_triplets))
        
        return intersection / union

    def coverage_score(self, retrieved: List[Dict], gold: List[Dict]) -> Dict[str, float]:
        """
        Calculate coverage scores for entities and relations
        Args:
            retrieved: List of retrieved edges from AQL query
            gold: List of ground truth edges
        Returns:
            Dictionary with entity coverage and relation coverage scores
        """
        # Get all unique entities and relations from gold standard
        gold_entities = set()
        gold_relations = set()
        for edge in gold:
            gold_entities.add(edge['head'])
            gold_entities.add(edge['tail'])
            gold_relations.add(edge['relation'])
            
        # Get all unique entities and relations from retrieved results
        retrieved_entities = set()
        retrieved_relations = set()
        for edge in retrieved:
            retrieved_entities.add(edge['head'])
            retrieved_entities.add(edge['tail'])
            retrieved_relations.add(edge['relation'])
            
        # Calculate coverage scores
        entity_coverage = len(retrieved_entities.intersection(gold_entities)) / len(gold_entities) if gold_entities else 0.0
        relation_coverage = len(retrieved_relations.intersection(gold_relations)) / len(gold_relations) if gold_relations else 0.0
        
        return {
            'entity_coverage': entity_coverage,
            'relation_coverage': relation_coverage
        }

    def evaluate(self, retrieved: List[Dict], gold: List[Dict], k_values: List[int] = [1, 3, 5, 10]) -> Dict:
        """
        Run all evaluation metrics
        Args:
            retrieved: List of retrieved edges from AQL query
            gold: List of ground truth edges
            k_values: List of k values to evaluate precision/recall/F1 at
        Returns:
            Dictionary containing all evaluation metrics
        """
        results = {}
        
        # Calculate precision, recall, and F1 at different k values
        for k in k_values:
            results[f'precision@{k}'] = self.precision_at_k(retrieved, gold, k)
            results[f'recall@{k}'] = self.recall_at_k(retrieved, gold, k)
            results[f'f1@{k}'] = self.f1_at_k(retrieved, gold, k)
            
        # Calculate Jaccard similarity
        results['jaccard_similarity'] = self.jaccard_similarity(retrieved, gold)
        
        # Calculate coverage scores
        coverage = self.coverage_score(retrieved, gold)
        results.update(coverage)
        
        return results

    def evaluate_aql_generation(self, benchmark_file: str) -> Dict:
        """
        Evaluate AQL query generation by comparing generated queries with reference queries
        in the benchmark file using BLEU score for similarity measurement.
        
        Args:
            benchmark_file: Path to JSON file containing benchmark queries with both
                          natural language queries and reference AQL queries
            
        Returns:
            Dictionary containing evaluation metrics for AQL generation including BLEU scores
        """
        # Load benchmark queries
        with open(benchmark_file, 'r') as f:
            benchmarks = json.load(f)
            
        results = {
            'exact_match': 0,
            'total_queries': len(benchmarks),
            'bleu_scores': [],
            'average_bleu': 0.0,
            'exact_match_rate': 0.0,
            'query_results': []
        }
        
        for benchmark in benchmarks[:3]:
            # Get natural language query and reference AQL query
            natural_query = benchmark['query']
            reference_aql = benchmark['aql_query']
            
            # Generate AQL query from natural language query
            _, generated_aql = text_to_aql_to_text(natural_query, eval=True)
            
            # Compare generated AQL with reference AQL
            is_exact_match = generated_aql.strip() == reference_aql.strip()
            if is_exact_match:
                results['exact_match'] += 1
            
            # Calculate BLEU score
            # Split queries into tokens (words and special characters)
            generated_tokens = [token for token in generated_aql.split()]
            reference_tokens = [token for token in reference_aql.split()]
            
            # Calculate BLEU score with smoothing
            bleu_score = sentence_bleu(
                [reference_tokens],
                generated_tokens,
                smoothing_function=self.smoothing
            )
            results['bleu_scores'].append(bleu_score)
            
            # Store detailed results for each query
            results['query_results'].append({
                'natural_query': natural_query,
                'generated_aql': generated_aql,
                'reference_aql': reference_aql,
                'bleu_score': bleu_score,
                'is_exact_match': is_exact_match
            })
        
        # Calculate average BLEU score
        results['average_bleu'] = np.mean(results['bleu_scores']) if results['bleu_scores'] else 0.0
        results['exact_match_rate'] = results['exact_match'] / results['total_queries'] if results['total_queries'] > 0 else 0.0

        print(results)
        
        return results 