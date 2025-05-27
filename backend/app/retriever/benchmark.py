"""
Benchmarking module for SocioGraph Phase 4 performance improvements.

This module provides benchmarking functions to measure the performance
improvements from the EmbeddingSingleton integration and optimizations.
"""

import time
import statistics
from typing import List, Dict, Any, Callable
from pathlib import Path
import json

from app.core.singletons import get_logger, embed_texts
from app.retriever.vector_utils import (
    text_similarity, 
    parallel_text_similarity,
    batch_similarity,
    parallel_batch_similarity
)
from app.retriever.sqlite_vec_utils import (
    get_entity_by_embedding,
    get_entities_by_embeddings
)
from app.retriever.embedding_cache import get_embedding_cache

# Initialize logger
_logger = get_logger()

class PerformanceBenchmark:
    """Class for running performance benchmarks."""
    
    def __init__(self):
        self.results = {}
        
    def time_function(self, func: Callable, *args, **kwargs) -> tuple:
        """Time a function execution.
        
        Args:
            func: Function to time
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Tuple of (result, execution_time)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    def benchmark_embedding_cache(self, texts: List[str], iterations: int = 5) -> Dict[str, Any]:
        """Benchmark embedding cache performance.
        
        Args:
            texts: List of texts to embed
            iterations: Number of iterations to run
            
        Returns:
            Dictionary with benchmark results
        """
        _logger.info(f"Benchmarking embedding cache with {len(texts)} texts, {iterations} iterations")
        
        # Clear cache to start fresh
        cache = get_embedding_cache()
        cache.clear()
        
        # Test cache misses (first run)
        miss_times = []
        for i in range(iterations):
            cache.clear()  # Ensure cache miss
            _, exec_time = self.time_function(embed_texts, texts, use_cache=True)
            miss_times.append(exec_time)
            
        # Test cache hits (subsequent runs)
        hit_times = []
        cache.clear()
        # Populate cache
        embed_texts(texts, use_cache=True)
        
        for i in range(iterations):
            _, exec_time = self.time_function(embed_texts, texts, use_cache=True)
            hit_times.append(exec_time)
          # Test without cache
        no_cache_times = []
        for i in range(iterations):
            _, exec_time = self.time_function(embed_texts, texts, use_cache=False)
            no_cache_times.append(exec_time)
        
        results = {
            "cache_miss_avg": statistics.mean(miss_times),
            "cache_hit_avg": statistics.mean(hit_times),
            "no_cache_avg": statistics.mean(no_cache_times),
            "speedup_vs_miss": statistics.mean(miss_times) / max(statistics.mean(hit_times), 1e-6),
            "speedup_vs_no_cache": statistics.mean(no_cache_times) / max(statistics.mean(hit_times), 1e-6),
            "cache_efficiency": (1 - statistics.mean(hit_times) / max(statistics.mean(miss_times), 1e-6)) * 100
        }
        
        _logger.info(f"Cache benchmark - Miss: {results['cache_miss_avg']:.4f}s, "
                    f"Hit: {results['cache_hit_avg']:.4f}s, "
                    f"Speedup: {results['speedup_vs_miss']:.2f}x")
        
        return results
    
    def benchmark_parallel_similarity(
        self, 
        query: str, 
        docs: List[str], 
        iterations: int = 3
    ) -> Dict[str, Any]:
        """Benchmark parallel vs sequential similarity calculation.
        
        Args:
            query: Query text
            docs: List of document texts
            iterations: Number of iterations to run
            
        Returns:
            Dictionary with benchmark results
        """
        _logger.info(f"Benchmarking similarity calculation with {len(docs)} documents")
        
        # Sequential similarity
        seq_times = []
        for i in range(iterations):
            _, exec_time = self.time_function(text_similarity, query, docs)
            seq_times.append(exec_time)
        
        # Parallel similarity
        par_times = []
        for i in range(iterations):
            _, exec_time = self.time_function(parallel_text_similarity, query, docs)
            par_times.append(exec_time)
            results = {
            "sequential_avg": statistics.mean(seq_times),
            "parallel_avg": statistics.mean(par_times),
            "speedup": statistics.mean(seq_times) / max(statistics.mean(par_times), 1e-6),
            "document_count": len(docs)
        }
        
        _logger.info(f"Similarity benchmark - Sequential: {results['sequential_avg']:.4f}s, "
                    f"Parallel: {results['parallel_avg']:.4f}s, "
                    f"Speedup: {results['speedup']:.2f}x")
        
        return results
    
    def benchmark_vector_search(
        self, 
        search_terms: List[str], 
        iterations: int = 3
    ) -> Dict[str, Any]:
        """Benchmark vector search performance.
        
        Args:
            search_terms: List of terms to search for
            iterations: Number of iterations to run
            
        Returns:
            Dictionary with benchmark results
        """
        _logger.info(f"Benchmarking vector search with {len(search_terms)} terms")
        
        # Individual searches
        individual_times = []
        for i in range(iterations):
            start_time = time.time()
            for term in search_terms:
                get_entity_by_embedding(term, use_parallel=False)
            end_time = time.time()
            individual_times.append(end_time - start_time)
        
        # Parallel individual searches
        parallel_individual_times = []
        for i in range(iterations):
            start_time = time.time()
            for term in search_terms:
                get_entity_by_embedding(term, use_parallel=True)
            end_time = time.time()
            parallel_individual_times.append(end_time - start_time)
          # Batch search
        batch_times = []
        for i in range(iterations):
            _, exec_time = self.time_function(get_entities_by_embeddings, search_terms)
            batch_times.append(exec_time)
        
        results = {
            "individual_avg": statistics.mean(individual_times),
            "parallel_individual_avg": statistics.mean(parallel_individual_times),
            "batch_avg": statistics.mean(batch_times),
            "speedup_parallel": statistics.mean(individual_times) / max(statistics.mean(parallel_individual_times), 1e-6),
            "speedup_batch": statistics.mean(individual_times) / max(statistics.mean(batch_times), 1e-6),
            "search_count": len(search_terms)
        }
        
        _logger.info(f"Vector search benchmark - Individual: {results['individual_avg']:.4f}s, "
                    f"Parallel: {results['parallel_individual_avg']:.4f}s, "
                    f"Batch: {results['batch_avg']:.4f}s")
        
        return results
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run a comprehensive benchmark of all optimizations.
        
        Returns:
            Dictionary with all benchmark results
        """
        _logger.info("Starting comprehensive performance benchmark...")
        
        # Test data
        test_texts = [
            "Climate change impacts on biodiversity",
            "Machine learning applications in healthcare",
            "Renewable energy technologies and sustainability",
            "Urban planning and smart city development",
            "Artificial intelligence ethics and governance",
            "Global economic trends and market analysis",
            "Environmental conservation strategies",
            "Digital transformation in business",
            "Healthcare innovation and telemedicine",
            "Educational technology and remote learning"
        ]
        
        large_doc_set = test_texts * 10  # 100 documents
        
        search_terms = [
            "climate change",
            "machine learning", 
            "renewable energy",
            "urban planning",
            "artificial intelligence"
        ]
        
        # Run benchmarks
        results = {
            "embedding_cache": self.benchmark_embedding_cache(test_texts),
            "parallel_similarity_small": self.benchmark_parallel_similarity(
                "What is the impact of technology?", test_texts
            ),
            "parallel_similarity_large": self.benchmark_parallel_similarity(
                "What is the impact of technology?", large_doc_set
            ),
            "vector_search": self.benchmark_vector_search(search_terms),
            "metadata": {
                "timestamp": time.time(),
                "test_text_count": len(test_texts),
                "large_doc_count": len(large_doc_set),
                "search_term_count": len(search_terms)
            }
        }
        
        _logger.info("Comprehensive benchmark completed")
        return results
    def save_results(self, results: Dict[str, Any], filepath: str = "benchmark_results.json"):
        """Save benchmark results to a JSON file.
        
        Args:
            results: Benchmark results dictionary
            filepath: Path to save the results file
        """
        filepath_obj = Path(filepath)
        with open(filepath_obj, 'w') as f:
            json.dump(results, f, indent=2)
        _logger.info(f"Benchmark results saved to {filepath_obj}")

def run_benchmark():
    """Run the benchmark and save results."""
    benchmark = PerformanceBenchmark()
    results = benchmark.run_comprehensive_benchmark()
    benchmark.save_results(results)
    return results

if __name__ == "__main__":
    run_benchmark()
