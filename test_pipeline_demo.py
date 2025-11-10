"""
Sample Test Runner for Snowflake Cortex GenAI Pipeline
This script demonstrates the pipeline with sample data when Snowflake credentials are not available.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simulate_snowflake_environment():
    """Simulate Snowflake environment for testing"""
    logger.info("=== SNOWFLAKE CORTEX GenAI PIPELINE - DEMO MODE ===")
    logger.info("Simulating pipeline execution with sample data...")
    
    return {
        "account": "demo-account",
        "user": "demo-user", 
        "database": "GENAI_DEMO",
        "schema": "CORTEX",
        "warehouse": "COMPUTE_WH"
    }

def simulate_document_ingestion():
    """Simulate document ingestion process"""
    logger.info("\n1. DOCUMENT INGESTION SIMULATION")
    logger.info("-" * 50)
    
    sample_docs = [
        {
            "id": "doc_001",
            "title": "TechCorp Company Overview", 
            "content": "TechCorp is a leading technology company...",
            "type": "company_info",
            "size_kb": 2.3
        },
        {
            "id": "doc_002", 
            "title": "CloudAI Platform User Guide",
            "content": "The CloudAI Platform is TechCorp's flagship...",
            "type": "product_docs",
            "size_kb": 4.1
        },
        {
            "id": "doc_003",
            "title": "System Architecture and Requirements", 
            "content": "TechCorp's infrastructure is built on modern...",
            "type": "technical_specs",
            "size_kb": 3.7
        },
        {
            "id": "doc_004",
            "title": "Customer Success Stories",
            "content": "RetailMax Success Story: RetailMax implemented...",
            "type": "case_studies", 
            "size_kb": 5.2
        }
    ]
    
    for doc in sample_docs:
        logger.info(f"✓ Ingested: {doc['title']} ({doc['size_kb']} KB)")
    
    logger.info(f"📊 Total documents processed: {len(sample_docs)}")
    return sample_docs

def simulate_embedding_generation(docs: List[Dict]):
    """Simulate vector embedding generation"""
    logger.info("\n2. EMBEDDING GENERATION SIMULATION") 
    logger.info("-" * 50)
    
    embeddings = []
    for doc in docs:
        # Simulate chunking
        chunks = max(1, int(doc['size_kb'] / 0.5))  # ~0.5KB per chunk
        
        for i in range(chunks):
            embedding = {
                "doc_id": doc['id'],
                "chunk_id": f"{doc['id']}_chunk_{i+1}",
                "text": f"Chunk {i+1} from {doc['title']}...",
                "embedding": f"[768-dimensional vector from CORTEX.EMBED_TEXT_768]",
                "processing_time_ms": 150 + (i * 10)
            }
            embeddings.append(embedding)
            logger.info(f"✓ Generated embedding: {embedding['chunk_id']}")
    
    logger.info(f"📊 Total embeddings created: {len(embeddings)}")
    logger.info(f"⚡ Average processing time: {sum(e['processing_time_ms'] for e in embeddings) / len(embeddings):.1f}ms")
    return embeddings

def simulate_query_processing(embeddings: List[Dict]):
    """Simulate query processing and semantic search"""
    logger.info("\n3. QUERY PROCESSING SIMULATION")
    logger.info("-" * 50)
    
    sample_queries = [
        "What are TechCorp's main business divisions?",
        "How much does the CloudAI platform cost?", 
        "What security features does TechCorp provide?",
        "Tell me about customer success stories"
    ]
    
    results = []
    
    for query in sample_queries:
        logger.info(f"\n🔍 Processing query: '{query}'")
        
        # Simulate query embedding
        query_embedding_time = 125
        logger.info(f"  ✓ Query embedded via CORTEX.EMBED_TEXT_768 ({query_embedding_time}ms)")
        
        # Simulate similarity search
        search_time = 45
        top_matches = [
            {"chunk_id": "doc_001_chunk_1", "similarity": 0.89},
            {"chunk_id": "doc_002_chunk_2", "similarity": 0.76}, 
            {"chunk_id": "doc_003_chunk_1", "similarity": 0.72}
        ]
        logger.info(f"  ✓ Found {len(top_matches)} similar chunks via VECTOR_COSINE_SIMILARITY ({search_time}ms)")
        
        # Simulate LLM completion
        completion_time = 850
        response = f"Based on the documents, {query.lower().replace('?', '')}... [Generated via CORTEX.COMPLETE]"
        logger.info(f"  ✓ Generated response via CORTEX.COMPLETE ({completion_time}ms)")
        
        total_time = query_embedding_time + search_time + completion_time
        
        result = {
            "query": query,
            "response": response,
            "matches": top_matches,
            "total_time_ms": total_time,
            "timestamp": datetime.now().isoformat()
        }
        results.append(result)
        
        logger.info(f"  📊 Total response time: {total_time}ms")
    
    return results

def simulate_telemetry_collection(docs: List[Dict], embeddings: List[Dict], queries: List[Dict]):
    """Simulate telemetry and monitoring"""
    logger.info("\n4. TELEMETRY & MONITORING SIMULATION")
    logger.info("-" * 50)
    
    # Calculate metrics
    total_docs = len(docs)
    total_embeddings = len(embeddings)
    total_queries = len(queries)
    
    avg_query_time = sum(q['total_time_ms'] for q in queries) / len(queries)
    success_rate = 100.0  # All simulated queries successful
    
    # Simulate costs
    embedding_cost = total_embeddings * 0.001  # $0.001 per embedding
    query_cost = total_queries * 0.005        # $0.005 per query
    storage_cost = sum(doc['size_kb'] for doc in docs) * 0.0001  # $0.0001 per KB
    
    total_cost = embedding_cost + query_cost + storage_cost
    
    metrics = {
        "performance": {
            "total_documents": total_docs,
            "total_embeddings": total_embeddings,
            "total_queries": total_queries,
            "avg_response_time_ms": round(avg_query_time, 1),
            "success_rate_percent": success_rate
        },
        "costs": {
            "embedding_operations": round(embedding_cost, 4),
            "query_operations": round(query_cost, 4), 
            "storage": round(storage_cost, 4),
            "total_usd": round(total_cost, 4)
        }
    }
    
    logger.info("📈 PERFORMANCE METRICS:")
    logger.info(f"  • Documents processed: {metrics['performance']['total_documents']}")
    logger.info(f"  • Embeddings generated: {metrics['performance']['total_embeddings']}")
    logger.info(f"  • Queries processed: {metrics['performance']['total_queries']}")
    logger.info(f"  • Avg response time: {metrics['performance']['avg_response_time_ms']}ms")
    logger.info(f"  • Success rate: {metrics['performance']['success_rate_percent']}%")
    
    logger.info("\n💰 COST BREAKDOWN:")
    logger.info(f"  • Embedding operations: ${metrics['costs']['embedding_operations']}")
    logger.info(f"  • Query operations: ${metrics['costs']['query_operations']}")
    logger.info(f"  • Storage costs: ${metrics['costs']['storage']}")
    logger.info(f"  • Total cost: ${metrics['costs']['total_usd']}")
    
    return metrics

def simulate_dashboard_data(metrics: Dict):
    """Generate sample dashboard data"""
    logger.info("\n5. DASHBOARD SIMULATION")
    logger.info("-" * 50)
    
    dashboard_url = "http://localhost:8501"  # Streamlit default port
    
    logger.info("📊 Dashboard features available:")
    logger.info(f"  • Real-time performance monitoring")
    logger.info(f"  • Cost analysis and trends")
    logger.info(f"  • Query testing interface") 
    logger.info(f"  • Telemetry visualization")
    logger.info(f"\n🌐 Dashboard would be available at: {dashboard_url}")
    
    return {"dashboard_url": dashboard_url, "status": "ready"}

def main():
    """Run the complete simulation"""
    try:
        # Setup
        env = simulate_snowflake_environment()
        
        # Pipeline simulation
        docs = simulate_document_ingestion()
        embeddings = simulate_embedding_generation(docs)  
        queries = simulate_query_processing(embeddings)
        metrics = simulate_telemetry_collection(docs, embeddings, queries)
        dashboard = simulate_dashboard_data(metrics)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("🎉 PIPELINE SIMULATION COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info("\nSUMMARY:")
        logger.info(f"✓ Processed {len(docs)} documents")
        logger.info(f"✓ Generated {len(embeddings)} embeddings") 
        logger.info(f"✓ Handled {len(queries)} queries")
        logger.info(f"✓ Average response time: {metrics['performance']['avg_response_time_ms']}ms")
        logger.info(f"✓ Total cost: ${metrics['costs']['total_usd']}")
        
        logger.info("\n📋 TO RUN WITH REAL SNOWFLAKE:")
        logger.info("1. Update config/.env with your Snowflake credentials")
        logger.info("2. Run: python3 src/utils.py (test connection)")
        logger.info("3. Run: python3 src/ingest_loader.py (load documents)")
        logger.info("4. Run: python3 src/embed_generator.py (generate embeddings)")
        logger.info("5. Run: python3 src/cortex_query.py (test queries)")
        logger.info("6. Run: streamlit run src/dashboard_plot.py (launch dashboard)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Simulation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)