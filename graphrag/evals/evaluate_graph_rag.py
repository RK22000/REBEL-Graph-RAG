import json
from typing import List, Dict
from graph_evaluation import GraphEvaluator
import pandas as pd
from arango import ArangoClient

class GraphRAGEvaluator:
    def __init__(self, arango_url: str, username: str, password: str, db_name: str):
        """Initialize the evaluator with ArangoDB connection details"""
        self.client = ArangoClient(hosts=arango_url)
        self.db = self.client.db(db_name, username=username, password=password)
        self.evaluator = GraphEvaluator()

    def load_benchmark_queries(self, benchmark_file: str) -> List[Dict]:
        """Load benchmark queries and their ground truth answers"""
        with open(benchmark_file, 'r') as f:
            return json.load(f)

    def execute_aql_query(self, query: str) -> List[Dict]:
        """Execute AQL query and return results"""
        cursor = self.db.aql.execute(query)
        return [doc for doc in cursor]

    def evaluate_benchmark(self, benchmark_file: str, output_file: str):
        """
        Evaluate the Graph RAG system on benchmark queries
        Args:
            benchmark_file: Path to JSON file containing benchmark queries and ground truth
            output_file: Path to save evaluation results
        """
        # Load benchmark queries
        benchmark_data = self.load_benchmark_queries(benchmark_file)
        
        results = []
        for query_data in benchmark_data:
            # Execute AQL query
            retrieved_results = self.execute_aql_query(query_data['aql_query'])
            
            # Get ground truth
            gold_standard = query_data['ground_truth']
            
            # Evaluate results
            metrics = self.evaluator.evaluate(retrieved_results, gold_standard)
            
            # Add query information
            metrics['query'] = query_data['query']
            metrics['aql_query'] = query_data['aql_query']
            
            results.append(metrics)
        
        # Convert results to DataFrame and save
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False)
        
        # Print summary statistics
        print("\nEvaluation Summary:")
        print("==================")
        for metric in ['precision@1', 'recall@1', 'f1@1', 'jaccard_similarity', 'entity_coverage', 'relation_coverage']:
            if metric in df.columns:
                mean_value = df[metric].mean()
                print(f"{metric}: {mean_value:.4f}")

def main():
    # Example usage
    evaluator = GraphRAGEvaluator(
        arango_url="http://localhost:8529",
        username="root",
        password="password",
        db_name="your_database"
    )
    
    evaluator.evaluate_benchmark(
        benchmark_file="benchmark_queries.json",
        output_file="evaluation_results.csv"
    )

if __name__ == "__main__":
    main() 