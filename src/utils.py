"""
Utility functions for Snowflake Cortex GenAI Pipeline
Provides session management, configuration loading, and common helpers.
"""

import os
import logging
import yaml
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from snowflake.snowpark import Session
from snowflake.snowpark.exceptions import SnowparkSessionException
import snowflake.connector


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SnowflakeConnectionManager:
    """Manages Snowflake connections and sessions"""
    
    def __init__(self, config_path: str = "config/creds.env"):
        """Initialize connection manager with configuration"""
        self.config_path = config_path
        self.session = None
        self.connection = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment file"""
        if os.path.exists(self.config_path):
            load_dotenv(self.config_path)
            logger.info(f"Loaded configuration from {self.config_path}")
        else:
            logger.warning(f"Config file not found: {self.config_path}")
            
    def get_connection_params(self) -> Dict[str, str]:
        """Get Snowflake connection parameters from environment"""
        required_params = {
            'account': os.getenv('SF_ACCOUNT'),
            'user': os.getenv('SF_USER'),
            'password': os.getenv('SF_PASSWORD'),
            'role': os.getenv('SF_ROLE', 'ACCOUNTADMIN'),
            'warehouse': os.getenv('SF_WAREHOUSE', 'GENAI_WH'),
            'database': os.getenv('SF_DATABASE', 'GENAI_DB'),
            'schema': os.getenv('SF_SCHEMA', 'PUBLIC')
        }
        
        # Filter out None values
        params = {k: v for k, v in required_params.items() if v is not None}
        
        if len(params) < 3:  # At minimum need account, user, password
            raise ValueError("Missing required Snowflake connection parameters. Check your .env file.")
            
        return params
    
    def create_session(self) -> Session:
        """Create and return Snowflake Snowpark session"""
        if self.session:
            return self.session
            
        try:
            connection_params = self.get_connection_params()
            self.session = Session.builder.configs(connection_params).create()
            logger.info("Successfully created Snowpark session")
            return self.session
            
        except SnowparkSessionException as e:
            logger.error(f"Failed to create Snowpark session: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating session: {e}")
            raise
    
    def create_connection(self):
        """Create raw Snowflake connector (for non-Snowpark operations)"""
        if self.connection:
            return self.connection
            
        try:
            connection_params = self.get_connection_params()
            self.connection = snowflake.connector.connect(**connection_params)
            logger.info("Successfully created Snowflake connection")
            return self.connection
            
        except Exception as e:
            logger.error(f"Failed to create Snowflake connection: {e}")
            raise
    
    def close(self):
        """Close all connections"""
        if self.session:
            self.session.close()
            self.session = None
            
        if self.connection:
            self.connection.close()
            self.connection = None
            
        logger.info("Closed all Snowflake connections")


def load_settings(settings_path: str = "config/settings.yaml") -> Dict[str, Any]:
    """Load YAML configuration settings"""
    try:
        with open(settings_path, 'r') as file:
            settings = yaml.safe_load(file)
            logger.info(f"Loaded settings from {settings_path}")
            return settings
    except FileNotFoundError:
        logger.warning(f"Settings file not found: {settings_path}")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML settings: {e}")
        raise


def format_query_results(results, max_rows: int = 10) -> str:
    """Format Snowpark DataFrame results for display"""
    if not results:
        return "No results found"
        
    try:
        # Convert to pandas for easier formatting
        df = results.limit(max_rows).to_pandas()
        return df.to_string(index=False)
    except Exception as e:
        logger.error(f"Error formatting results: {e}")
        return str(results)


def validate_cortex_model(model_name: str) -> bool:
    """Validate if the specified Cortex model is available"""
    # List of supported Cortex models (as of 2025)
    supported_embedding_models = [
        'text-embedding-ada-002',
        'text-embedding-3-small',
        'text-embedding-3-large'
    ]
    
    supported_llm_models = [
        'mistral-large',
        'mistral-7b',
        'llama2-70b-chat',
        'gemma-7b',
        'mixtral-8x7b',
        'reka-flash'
    ]
    
    all_models = supported_embedding_models + supported_llm_models
    return model_name in all_models


def calculate_token_cost(token_count: int, model_name: str) -> float:
    """Calculate estimated cost per 1k tokens for Cortex models"""
    # Approximate costs (in USD per 1k tokens) - update with actual pricing
    model_costs = {
        'text-embedding-ada-002': 0.0001,
        'text-embedding-3-small': 0.00002,
        'text-embedding-3-large': 0.00013,
        'mistral-large': 0.008,
        'mistral-7b': 0.0002,
        'llama2-70b-chat': 0.0007,
        'gemma-7b': 0.0002,
        'mixtral-8x7b': 0.0007,
        'reka-flash': 0.0005
    }
    
    cost_per_1k = model_costs.get(model_name, 0.001)  # Default fallback
    return (token_count / 1000) * cost_per_1k


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup consistent logging across modules"""
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    level = log_levels.get(log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Add console handler if not already present
    if not root_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    return logging.getLogger(__name__)


# Global connection manager instance
connection_manager = SnowflakeConnectionManager()


def get_session() -> Session:
    """Get global Snowpark session"""
    return connection_manager.create_session()


def get_connection():
    """Get global Snowflake connection"""
    return connection_manager.create_connection()


if __name__ == "__main__":
    # Test connection
    print("Testing Snowflake connection...")
    try:
        session = get_session()
        result = session.sql("SELECT CURRENT_VERSION()").collect()
        print(f"Connection successful! Snowflake version: {result[0][0]}")
        
        # Test Cortex availability
        cortex_test = session.sql("SELECT SNOWFLAKE.CORTEX_EMBEDDINGS('text-embedding-ada-002', 'test') IS NOT NULL AS cortex_available").collect()
        if cortex_test[0][0]:
            print("Cortex functions are available!")
        else:
            print("Cortex functions not available - check your Snowflake edition")
            
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Please check your credentials in config/creds.env")
    finally:
        connection_manager.close()