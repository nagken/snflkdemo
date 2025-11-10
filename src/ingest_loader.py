"""
Data Ingestion and Loading Module for Snowflake Cortex GenAI Pipeline
Handles uploading files to Snowflake stage and loading into tables.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit
from snowflake.snowpark.types import StructType, StructField, StringType
import PyPDF2
import docx

from utils import get_session, load_settings, setup_logging

logger = setup_logging()


class DocumentIngestor:
    """Handles document ingestion and processing for Cortex pipeline"""
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize with Snowpark session"""
        self.session = session or get_session()
        self.settings = load_settings()
        self.stage_name = self.settings.get('data', {}).get('raw_stage', '@media_raw')
        self.table_name = self.settings.get('data', {}).get('tables', {}).get('raw', 'media_raw')
        
    def setup_infrastructure(self):
        """Create necessary database objects (stage, tables)"""
        try:
            # Create stage for file uploads
            stage_sql = f"""
            CREATE STAGE IF NOT EXISTS {self.stage_name}
            DIRECTORY = (ENABLE = TRUE)
            COMMENT = 'Stage for GenAI document uploads'
            """
            
            self.session.sql(stage_sql).collect()
            logger.info(f"Created/verified stage: {self.stage_name}")
            
            # Create raw documents table
            table_sql = f"""
            CREATE OR REPLACE TABLE {self.table_name} (
                doc_id STRING PRIMARY KEY,
                filename STRING,
                content STRING,
                file_type STRING,
                file_size_bytes NUMBER,
                upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                metadata VARIANT
            )
            COMMENT = 'Raw document content for GenAI processing'
            """
            
            self.session.sql(table_sql).collect()
            logger.info(f"Created table: {self.table_name}")
            
            # Create telemetry table
            telemetry_sql = """
            CREATE OR REPLACE TABLE genai_telemetry (
                telemetry_id STRING PRIMARY KEY DEFAULT UUID_STRING(),
                operation_type STRING,
                model_name STRING,
                input_tokens NUMBER,
                output_tokens NUMBER,
                latency_ms NUMBER,
                cost_usd DECIMAL(10,6),
                success_flag BOOLEAN,
                error_message STRING,
                query_text STRING,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                session_id STRING,
                metadata VARIANT
            )
            COMMENT = 'Telemetry data for GenAI operations'
            """
            
            self.session.sql(telemetry_sql).collect()
            logger.info("Created telemetry table: genai_telemetry")
            
        except Exception as e:
            logger.error(f"Failed to setup infrastructure: {e}")
            raise
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF text from {file_path}: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text content from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting DOCX text from {file_path}: {e}")
            return ""
    
    def extract_text_from_file(self, file_path: str) -> tuple[str, str]:
        """Extract text content from various file types"""
        file_path = Path(file_path)
        file_type = file_path.suffix.lower()
        
        if file_type == '.pdf':
            content = self.extract_text_from_pdf(str(file_path))
        elif file_type == '.docx':
            content = self.extract_text_from_docx(str(file_path))
        elif file_type in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            logger.warning(f"Unsupported file type: {file_type}")
            content = ""
        
        return content, file_type
    
    def upload_file_to_stage(self, file_path: str) -> bool:
        """Upload file to Snowflake stage"""
        try:
            # Upload file to stage
            put_sql = f"PUT file://{file_path} {self.stage_name} AUTO_COMPRESS=FALSE"
            result = self.session.sql(put_sql).collect()
            
            if result and result[0]['status'] == 'UPLOADED':
                logger.info(f"Uploaded file to stage: {file_path}")
                return True
            else:
                logger.error(f"Failed to upload file: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            return False
    
    def load_document(self, file_path: str, doc_id: Optional[str] = None) -> bool:
        """Load a single document into Snowflake"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            # Generate doc_id if not provided
            if not doc_id:
                doc_id = f"doc_{file_path.stem}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Extract text content
            content, file_type = self.extract_text_from_file(str(file_path))
            
            if not content.strip():
                logger.warning(f"No text content extracted from {file_path}")
                return False
            
            # Get file metadata
            file_stats = file_path.stat()
            metadata = {
                'original_path': str(file_path),
                'processed_timestamp': pd.Timestamp.now().isoformat(),
                'content_length': len(content),
                'extraction_method': 'automated'
            }
            
            # Insert into raw table
            insert_data = [{
                'doc_id': doc_id,
                'filename': file_path.name,
                'content': content,
                'file_type': file_type,
                'file_size_bytes': file_stats.st_size,
                'metadata': metadata
            }]
            
            # Create DataFrame and insert
            df = self.session.create_dataframe(insert_data)
            df.write.mode("append").save_as_table(self.table_name)
            
            logger.info(f"Loaded document: {doc_id} ({len(content)} chars)")
            return True
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            return False
    
    def load_sample_documents(self) -> bool:
        """Load sample documents for testing"""
        sample_docs = [
            {
                'doc_id': 'sample_ai_automation',
                'content': """
                Artificial Intelligence Automation in Enterprise
                
                AI automation is revolutionizing how businesses operate across industries. 
                Machine learning algorithms can now automate complex decision-making processes,
                from supply chain optimization to customer service interactions.
                
                Key benefits include:
                - 40% reduction in operational costs
                - 60% faster processing times  
                - 95% accuracy in routine tasks
                - 24/7 operational capability
                
                Popular AI automation tools include robotic process automation (RPA),
                natural language processing for document analysis, and predictive analytics
                for demand forecasting. Companies implementing AI automation report
                significant improvements in efficiency and customer satisfaction.
                """,
                'filename': 'ai_automation_guide.txt',
                'file_type': '.txt'
            },
            {
                'doc_id': 'sample_snowflake_cortex',
                'content': """
                Snowflake Cortex: Complete AI Platform
                
                Snowflake Cortex provides a comprehensive suite of AI and ML functions
                directly within the Snowflake Data Cloud. This eliminates the need
                to move data to external platforms for AI processing.
                
                Core Cortex Functions:
                - CORTEX_EMBEDDINGS: Generate vector embeddings from text
                - CORTEX_COMPLETE: LLM text completion and chat
                - CORTEX_TRANSLATE: Multi-language translation
                - CORTEX_SENTIMENT: Text sentiment analysis
                - CORTEX_SUMMARIZE: Document summarization
                
                Performance benchmarks show Cortex achieving sub-2-second response times
                for most queries with 97% success rates. Cost optimization through
                native integration provides up to 39% savings compared to external APIs.
                """,
                'filename': 'snowflake_cortex_overview.txt',
                'file_type': '.txt'
            },
            {
                'doc_id': 'sample_genai_strategy',
                'content': """
                Generative AI Strategy for Data Teams
                
                Building a successful GenAI strategy requires careful consideration
                of data governance, model selection, and deployment architecture.
                
                Strategic Pillars:
                1. Data Foundation: Clean, well-structured data pipelines
                2. Model Governance: Version control, testing, monitoring
                3. Security & Privacy: Data encryption, access controls
                4. Scalable Infrastructure: Auto-scaling, cost optimization
                5. User Experience: Intuitive interfaces, fast responses
                
                Best practices include starting with pilot projects, measuring ROI,
                and gradually expanding AI capabilities across the organization.
                Success metrics should include accuracy, latency, user adoption,
                and business impact measurement.
                """,
                'filename': 'genai_strategy_playbook.txt',
                'file_type': '.txt'
            }
        ]
        
        try:
            success_count = 0
            for doc in sample_docs:
                # Check if document already exists
                check_sql = f"SELECT COUNT(*) as cnt FROM {self.table_name} WHERE doc_id = '{doc['doc_id']}'"
                result = self.session.sql(check_sql).collect()
                
                if result[0]['CNT'] > 0:
                    logger.info(f"Document {doc['doc_id']} already exists, skipping...")
                    continue
                
                # Insert sample document
                insert_data = [{
                    'doc_id': doc['doc_id'],
                    'filename': doc['filename'],
                    'content': doc['content'].strip(),
                    'file_type': doc['file_type'],
                    'file_size_bytes': len(doc['content'].encode('utf-8')),
                    'metadata': {'source': 'sample_data', 'generated': True}
                }]
                
                df = self.session.create_dataframe(insert_data)
                df.write.mode("append").save_as_table(self.table_name)
                success_count += 1
                
            logger.info(f"Loaded {success_count} sample documents")
            return True
            
        except Exception as e:
            logger.error(f"Error loading sample documents: {e}")
            return False
    
    def batch_load_directory(self, directory_path: str) -> Dict[str, Any]:
        """Load all supported files from a directory"""
        directory_path = Path(directory_path)
        results = {
            'success_count': 0,
            'failed_count': 0,
            'processed_files': [],
            'errors': []
        }
        
        if not directory_path.exists():
            logger.error(f"Directory not found: {directory_path}")
            return results
        
        supported_extensions = ['.txt', '.pdf', '.docx', '.md']
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    if self.load_document(str(file_path)):
                        results['success_count'] += 1
                        results['processed_files'].append(str(file_path))
                    else:
                        results['failed_count'] += 1
                        results['errors'].append(f"Failed to load: {file_path}")
                        
                except Exception as e:
                    results['failed_count'] += 1
                    results['errors'].append(f"Error processing {file_path}: {e}")
        
        logger.info(f"Batch load complete: {results['success_count']} success, {results['failed_count']} failed")
        return results
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded documents"""
        try:
            stats_sql = f"""
            SELECT 
                COUNT(*) as total_documents,
                COUNT(DISTINCT file_type) as unique_file_types,
                AVG(LENGTH(content)) as avg_content_length,
                SUM(file_size_bytes) as total_size_bytes,
                MIN(upload_timestamp) as first_upload,
                MAX(upload_timestamp) as latest_upload
            FROM {self.table_name}
            """
            
            result = self.session.sql(stats_sql).collect()[0]
            
            return {
                'total_documents': result['TOTAL_DOCUMENTS'],
                'unique_file_types': result['UNIQUE_FILE_TYPES'], 
                'avg_content_length': round(result['AVG_CONTENT_LENGTH'] or 0, 2),
                'total_size_mb': round((result['TOTAL_SIZE_BYTES'] or 0) / 1024 / 1024, 2),
                'first_upload': result['FIRST_UPLOAD'],
                'latest_upload': result['LATEST_UPLOAD']
            }
            
        except Exception as e:
            logger.error(f"Error getting document stats: {e}")
            return {}


def main():
    """Main function for testing and CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Snowflake GenAI Document Ingestor')
    parser.add_argument('--setup', action='store_true', help='Setup database infrastructure')
    parser.add_argument('--load-samples', action='store_true', help='Load sample documents')
    parser.add_argument('--load-file', type=str, help='Load specific file')
    parser.add_argument('--load-dir', type=str, help='Load all files from directory')
    parser.add_argument('--stats', action='store_true', help='Show document statistics')
    
    args = parser.parse_args()
    
    try:
        ingestor = DocumentIngestor()
        
        if args.setup:
            print("Setting up database infrastructure...")
            ingestor.setup_infrastructure()
            print("Infrastructure setup complete!")
        
        if args.load_samples:
            print("Loading sample documents...")
            ingestor.load_sample_documents()
            print("Sample documents loaded!")
        
        if args.load_file:
            print(f"Loading file: {args.load_file}")
            if ingestor.load_document(args.load_file):
                print("File loaded successfully!")
            else:
                print("Failed to load file!")
        
        if args.load_dir:
            print(f"Loading directory: {args.load_dir}")
            results = ingestor.batch_load_directory(args.load_dir)
            print(f"Loaded {results['success_count']} files, {results['failed_count']} failed")
        
        if args.stats:
            print("Document Statistics:")
            stats = ingestor.get_document_stats()
            for key, value in stats.items():
                print(f"  {key}: {value}")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()