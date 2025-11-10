"""
Cortex Query Module for Snowflake GenAI Pipeline
Handles semantic search and LLM completion using Snowflake Cortex.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit

from utils import get_session, load_settings, setup_logging, calculate_token_cost, validate_cortex_model
from telemetry_task import TelemetryTracker

logger = setup_logging()


class CortexQueryEngine:
    """Handles semantic search and LLM queries using Snowflake Cortex"""
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize query engine with configuration"""
        self.session = session or get_session()
        self.settings = load_settings()
        
        # Model configuration
        self.embedding_model = self.settings.get('cortex', {}).get('embedding', {}).get('model', 'text-embedding-ada-002')
        self.llm_model = self.settings.get('cortex', {}).get('llm', {}).get('model', 'mistral-large')
        self.max_tokens = self.settings.get('cortex', {}).get('llm', {}).get('max_tokens', 4096)
        self.temperature = self.settings.get('cortex', {}).get('llm', {}).get('temperature', 0.7)
        self.top_p = self.settings.get('cortex', {}).get('llm', {}).get('top_p', 0.9)
        
        # Search configuration
        self.top_k = self.settings.get('cortex', {}).get('search', {}).get('top_k', 5)
        self.similarity_threshold = self.settings.get('cortex', {}).get('search', {}).get('similarity_threshold', 0.8)
        
        # Table names
        self.embeddings_table = self.settings.get('data', {}).get('tables', {}).get('embeddings', 'media_embeddings')
        
        # Initialize telemetry
        self.telemetry = TelemetryTracker(session=self.session)
        
        # Validate models
        if not validate_cortex_model(self.embedding_model):
            logger.warning(f"Embedding model may not be supported: {self.embedding_model}")
        if not validate_cortex_model(self.llm_model):
            logger.warning(f"LLM model may not be supported: {self.llm_model}")
    
    def generate_query_embedding(self, query: str) -> Tuple[List[float], Dict[str, Any]]:
        """Generate embedding for search query"""
        with self.telemetry.track_operation('query_embedding', self.embedding_model) as tracker:
            try:
                # Escape quotes and format query
                escaped_query = query.replace("'", "''")
                
                # Generate embedding using Cortex
                embedding_sql = f"""
                SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768('{self.embedding_model}', '{escaped_query}') as embedding
                """
                
                result = self.session.sql(embedding_sql).collect()
                
                if not result or not result[0]['EMBEDDING']:
                    raise Exception("Failed to generate query embedding")
                
                embedding = result[0]['EMBEDDING']
                
                # Calculate metrics
                token_count = len(query.split()) * 1.3  # Rough token estimation
                tracker.set_tokens(input_tokens=int(token_count))
                tracker.set_query(query)
                tracker.add_metadata(query_length=len(query))
                
                metrics = {
                    'token_count': int(token_count),
                    'embedding_dimension': len(embedding) if isinstance(embedding, list) else 768
                }
                
                return embedding, metrics
                
            except Exception as e:
                logger.error(f"Error generating query embedding: {e}")
                raise
    
    def semantic_search(self, query: str, top_k: Optional[int] = None, 
                       similarity_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Perform semantic search using vector similarity"""
        
        top_k = top_k or self.top_k
        similarity_threshold = similarity_threshold or self.similarity_threshold
        
        with self.telemetry.track_operation('semantic_search', 'vector_similarity') as tracker:
            try:
                # Generate query embedding
                query_embedding, embedding_metrics = self.generate_query_embedding(query)
                
                # Convert embedding to JSON string for SQL
                if isinstance(query_embedding, list):
                    embedding_json = str(query_embedding).replace("'", '"')
                else:
                    embedding_json = str(query_embedding)
                
                # Perform similarity search
                search_sql = f"""
                SELECT 
                    doc_id,
                    filename,
                    content_chunk,
                    chunk_index,
                    embedding_model,
                    token_count,
                    VECTOR_COSINE_SIMILARITY(embedding, PARSE_JSON('{embedding_json}')::ARRAY) as similarity_score,
                    embedding_timestamp
                FROM {self.embeddings_table}
                WHERE VECTOR_COSINE_SIMILARITY(embedding, PARSE_JSON('{embedding_json}')::ARRAY) >= {similarity_threshold}
                ORDER BY similarity_score DESC
                LIMIT {top_k}
                """
                
                results = self.session.sql(search_sql).collect()
                
                # Format results
                search_results = []
                for row in results:
                    search_results.append({
                        'doc_id': row['DOC_ID'],
                        'filename': row['FILENAME'],
                        'content_chunk': row['CONTENT_CHUNK'],
                        'chunk_index': row['CHUNK_INDEX'],
                        'similarity_score': float(row['SIMILARITY_SCORE']),
                        'token_count': row['TOKEN_COUNT'],
                        'embedding_model': row['EMBEDDING_MODEL'],
                        'embedding_timestamp': row['EMBEDDING_TIMESTAMP']
                    })
                
                # Update telemetry
                tracker.set_tokens(input_tokens=embedding_metrics['token_count'])
                tracker.set_query(query)
                tracker.add_metadata(
                    results_count=len(search_results),
                    top_k=top_k,
                    similarity_threshold=similarity_threshold,
                    best_score=search_results[0]['similarity_score'] if search_results else 0
                )
                
                logger.info(f"Semantic search found {len(search_results)} results for query: '{query[:50]}...'")
                return search_results
                
            except Exception as e:
                logger.error(f"Error in semantic search: {e}")
                raise
    
    def generate_completion(self, prompt: str, context_chunks: List[str] = None, 
                          max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> Dict[str, Any]:
        """Generate LLM completion using Cortex"""
        
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        
        with self.telemetry.track_operation('llm_completion', self.llm_model) as tracker:
            try:
                # Build context-enhanced prompt
                enhanced_prompt = self._build_enhanced_prompt(prompt, context_chunks)
                
                # Escape quotes for SQL
                escaped_prompt = enhanced_prompt.replace("'", "''")
                
                # Generate completion using Cortex
                completion_sql = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    '{self.llm_model}',
                    '{escaped_prompt}',
                    OBJECT_CONSTRUCT(
                        'max_tokens', {max_tokens},
                        'temperature', {temperature},
                        'top_p', {self.top_p}
                    )
                ) as completion
                """
                
                result = self.session.sql(completion_sql).collect()
                
                if not result or not result[0]['COMPLETION']:
                    raise Exception("No completion generated by Cortex")
                
                completion_text = result[0]['COMPLETION']
                
                # Estimate token counts
                input_tokens = len(enhanced_prompt.split()) * 1.3
                output_tokens = len(completion_text.split()) * 1.3
                
                # Update telemetry
                tracker.set_tokens(input_tokens=int(input_tokens), output_tokens=int(output_tokens))
                tracker.set_query(prompt)
                tracker.set_response(completion_text)
                tracker.add_metadata(
                    context_chunks_count=len(context_chunks) if context_chunks else 0,
                    prompt_length=len(enhanced_prompt),
                    completion_length=len(completion_text),
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                return {
                    'completion': completion_text,
                    'input_tokens': int(input_tokens),
                    'output_tokens': int(output_tokens),
                    'model': self.llm_model,
                    'temperature': temperature,
                    'enhanced_prompt': enhanced_prompt,
                    'context_chunks_used': len(context_chunks) if context_chunks else 0
                }
                
            except Exception as e:
                logger.error(f"Error generating completion: {e}")
                raise
    
    def _build_enhanced_prompt(self, user_query: str, context_chunks: List[str] = None) -> str:
        """Build context-enhanced prompt for better LLM responses"""
        
        # System instruction
        system_prompt = """You are a helpful AI assistant that answers questions based on provided context. 
Use the context information to provide accurate, relevant responses. If the context doesn't contain 
enough information to fully answer the question, say so clearly."""
        
        # Build prompt with context
        if context_chunks:
            context_text = "\n\n".join([f"Context {i+1}:\n{chunk}" for i, chunk in enumerate(context_chunks)])
            
            enhanced_prompt = f"""{system_prompt}

Context Information:
{context_text}

User Question: {user_query}

Please provide a comprehensive answer based on the context above:"""
        else:
            enhanced_prompt = f"""{system_prompt}

User Question: {user_query}

Please provide a helpful answer:"""
        
        return enhanced_prompt
    
    def query_with_context(self, query: str, use_search: bool = True, 
                          top_k: Optional[int] = None, temperature: Optional[float] = None) -> Dict[str, Any]:
        """Complete pipeline: search + context + LLM completion"""
        
        with self.telemetry.track_operation('complete_query_pipeline', 'full_pipeline') as tracker:
            try:
                start_time = time.time()
                
                # Step 1: Semantic search (if enabled)
                context_chunks = []
                search_results = []
                
                if use_search:
                    search_results = self.semantic_search(query, top_k=top_k)
                    context_chunks = [result['content_chunk'] for result in search_results]
                
                # Step 2: Generate completion with context
                completion_result = self.generate_completion(
                    query, 
                    context_chunks=context_chunks,
                    temperature=temperature
                )
                
                # Step 3: Compile final response
                total_latency_ms = (time.time() - start_time) * 1000
                
                response = {
                    'query': query,
                    'answer': completion_result['completion'],
                    'context_used': len(context_chunks) > 0,
                    'search_results': search_results,
                    'model_info': {
                        'embedding_model': self.embedding_model if use_search else None,
                        'llm_model': self.llm_model,
                        'temperature': completion_result['temperature']
                    },
                    'metrics': {
                        'total_latency_ms': round(total_latency_ms, 2),
                        'search_results_count': len(search_results),
                        'context_chunks_used': len(context_chunks),
                        'input_tokens': completion_result['input_tokens'],
                        'output_tokens': completion_result['output_tokens'],
                        'total_tokens': completion_result['input_tokens'] + completion_result['output_tokens']
                    },
                    'cost_estimate': {
                        'total_usd': calculate_token_cost(
                            completion_result['input_tokens'] + completion_result['output_tokens'], 
                            self.llm_model
                        )
                    }
                }
                
                # Update pipeline telemetry
                tracker.set_tokens(
                    input_tokens=completion_result['input_tokens'],
                    output_tokens=completion_result['output_tokens']
                )
                tracker.set_query(query)
                tracker.set_response(completion_result['completion'])
                tracker.add_metadata(
                    search_enabled=use_search,
                    context_chunks=len(context_chunks),
                    search_results=len(search_results),
                    pipeline_latency_ms=total_latency_ms
                )
                
                logger.info(f"Query pipeline complete: {total_latency_ms:.1f}ms, {len(context_chunks)} context chunks")
                return response
                
            except Exception as e:
                logger.error(f"Error in query pipeline: {e}")
                raise
    
    def batch_query(self, queries: List[str], use_search: bool = True) -> List[Dict[str, Any]]:
        """Process multiple queries in batch"""
        results = []
        
        logger.info(f"Processing batch of {len(queries)} queries...")
        
        for i, query in enumerate(queries):
            try:
                result = self.query_with_context(query, use_search=use_search)
                result['batch_index'] = i
                results.append(result)
                
                # Log progress
                if (i + 1) % 5 == 0:
                    logger.info(f"Processed {i + 1}/{len(queries)} queries")
                    
            except Exception as e:
                logger.error(f"Error processing query {i}: {query[:50]}... - {e}")
                results.append({
                    'query': query,
                    'batch_index': i,
                    'error': str(e),
                    'answer': None
                })
        
        logger.info(f"Batch processing complete: {len([r for r in results if 'error' not in r])}/{len(queries)} successful")
        return results
    
    def get_query_suggestions(self, partial_query: str) -> List[str]:
        """Get query suggestions based on existing document content"""
        try:
            # Simple approach: find similar content and suggest queries
            if len(partial_query.strip()) < 3:
                return []
            
            # Search for relevant chunks
            search_results = self.semantic_search(partial_query, top_k=3)
            
            suggestions = []
            for result in search_results:
                # Extract potential query phrases from content
                content = result['content_chunk']
                sentences = content.split('.')
                
                for sentence in sentences[:2]:  # Take first 2 sentences
                    sentence = sentence.strip()
                    if len(sentence) > 20 and len(sentence) < 100:
                        # Convert to question format
                        if not sentence.endswith('?'):
                            suggestion = f"What is {sentence.lower()}?"
                        else:
                            suggestion = sentence
                        
                        if suggestion not in suggestions:
                            suggestions.append(suggestion)
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error generating query suggestions: {e}")
            return []


def main():
    """Main function for testing and CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Snowflake Cortex Query Engine')
    parser.add_argument('--query', type=str, help='Query to process')
    parser.add_argument('--no-search', action='store_true', help='Disable semantic search')
    parser.add_argument('--batch-file', type=str, help='File with queries (one per line)')
    parser.add_argument('--top-k', type=int, default=5, help='Number of search results to use')
    parser.add_argument('--temperature', type=float, default=0.7, help='LLM temperature')
    parser.add_argument('--interactive', action='store_true', help='Interactive query mode')
    
    args = parser.parse_args()
    
    try:
        engine = CortexQueryEngine()
        
        if args.query:
            print(f"Processing query: {args.query}")
            result = engine.query_with_context(
                args.query, 
                use_search=not args.no_search,
                top_k=args.top_k,
                temperature=args.temperature
            )
            
            print(f"\nAnswer:\n{result['answer']}")
            print(f"\nMetrics:")
            for key, value in result['metrics'].items():
                print(f"  {key}: {value}")
        
        elif args.batch_file:
            print(f"Processing batch file: {args.batch_file}")
            with open(args.batch_file, 'r') as f:
                queries = [line.strip() for line in f if line.strip()]
            
            results = engine.batch_query(queries, use_search=not args.no_search)
            
            # Save results
            output_file = args.batch_file.replace('.txt', '_results.txt')
            with open(output_file, 'w') as f:
                for result in results:
                    f.write(f"Query: {result['query']}\n")
                    f.write(f"Answer: {result.get('answer', 'ERROR')}\n")
                    f.write("---\n")
            
            print(f"Results saved to: {output_file}")
        
        elif args.interactive:
            print("Interactive Query Mode (type 'quit' to exit)")
            while True:
                query = input("\nEnter your query: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if query:
                    try:
                        result = engine.query_with_context(
                            query,
                            use_search=not args.no_search,
                            top_k=args.top_k,
                            temperature=args.temperature
                        )
                        print(f"\nAnswer:\n{result['answer']}")
                        print(f"Latency: {result['metrics']['total_latency_ms']}ms")
                    except Exception as e:
                        print(f"Error: {e}")
        else:
            # Demo queries
            demo_queries = [
                "What are the benefits of AI automation?",
                "How does Snowflake Cortex work?",
                "What is a good GenAI strategy?"
            ]
            
            print("Running demo queries...")
            for query in demo_queries:
                print(f"\nQuery: {query}")
                try:
                    result = engine.query_with_context(query, top_k=args.top_k)
                    print(f"Answer: {result['answer'][:200]}...")
                    print(f"Latency: {result['metrics']['total_latency_ms']}ms")
                except Exception as e:
                    print(f"Error: {e}")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()