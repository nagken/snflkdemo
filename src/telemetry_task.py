"""
Telemetry Tracking Module for Snowflake Cortex GenAI Pipeline
Tracks performance metrics, costs, and operational telemetry.
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional
import pandas as pd
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit

from utils import get_session, load_settings, setup_logging, calculate_token_cost

logger = setup_logging()


class TelemetryTracker:
    """Tracks and logs telemetry data for GenAI operations"""
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize telemetry tracker"""
        self.session = session or get_session()
        self.settings = load_settings()
        self.telemetry_table = self.settings.get('data', {}).get('tables', {}).get('telemetry', 'genai_telemetry')
        self.batch_size = self.settings.get('telemetry', {}).get('batch_size', 50)
        self.session_id = str(uuid.uuid4())
        
        # In-memory batch for performance
        self.batch_buffer = []
        
    def setup_telemetry_table(self):
        """Create telemetry table if not exists"""
        try:
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.telemetry_table} (
                telemetry_id STRING PRIMARY KEY DEFAULT UUID_STRING(),
                operation_type STRING NOT NULL,
                model_name STRING,
                input_tokens NUMBER,
                output_tokens NUMBER,
                total_tokens NUMBER GENERATED ALWAYS AS (COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0)),
                latency_ms NUMBER,
                cost_usd DECIMAL(10,6),
                success_flag BOOLEAN NOT NULL,
                error_message STRING,
                query_text STRING,
                response_text STRING,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
                session_id STRING,
                user_id STRING DEFAULT CURRENT_USER(),
                metadata VARIANT
            )
            COMMENT = 'Telemetry tracking for GenAI operations'
            """
            
            self.session.sql(create_sql).collect()
            logger.info(f"Telemetry table ready: {self.telemetry_table}")
            
        except Exception as e:
            logger.error(f"Failed to setup telemetry table: {e}")
            raise
    
    def log_operation(self, 
                     operation_type: str,
                     model_name: str = None,
                     input_tokens: int = 0,
                     output_tokens: int = 0,
                     latency_ms: float = 0.0,
                     cost_usd: float = 0.0,
                     success_flag: bool = True,
                     error_message: str = None,
                     query_text: str = None,
                     response_text: str = None,
                     metadata: Dict[str, Any] = None) -> str:
        """Log a single operation to telemetry"""
        
        telemetry_id = str(uuid.uuid4())
        
        try:
            # Prepare telemetry record
            record = {
                'telemetry_id': telemetry_id,
                'operation_type': operation_type,
                'model_name': model_name,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'latency_ms': round(latency_ms, 2),
                'cost_usd': round(cost_usd, 6),
                'success_flag': success_flag,
                'error_message': error_message,
                'query_text': query_text[:1000] if query_text else None,  # Truncate long queries
                'response_text': response_text[:2000] if response_text else None,  # Truncate long responses
                'session_id': self.session_id,
                'metadata': metadata or {}
            }
            
            # Add to batch buffer
            self.batch_buffer.append(record)
            
            # Flush if batch is full
            if len(self.batch_buffer) >= self.batch_size:
                self._flush_batch()
            
            return telemetry_id
            
        except Exception as e:
            logger.error(f"Error logging telemetry: {e}")
            return telemetry_id  # Return ID even if logging fails
    
    def _flush_batch(self):
        """Flush batch buffer to Snowflake"""
        if not self.batch_buffer:
            return
        
        try:
            df = self.session.create_dataframe(self.batch_buffer)
            df.write.mode("append").save_as_table(self.telemetry_table)
            
            logger.debug(f"Flushed {len(self.batch_buffer)} telemetry records")
            self.batch_buffer.clear()
            
        except Exception as e:
            logger.error(f"Error flushing telemetry batch: {e}")
            # Keep buffer for retry
    
    def flush(self):
        """Manually flush any pending telemetry records"""
        self._flush_batch()
    
    def track_operation(self, operation_type: str, model_name: str = None):
        """Context manager for automatic operation tracking"""
        return OperationTracker(self, operation_type, model_name)
    
    def get_performance_metrics(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get performance metrics for the last N hours"""
        try:
            metrics_sql = f"""
            SELECT 
                operation_type,
                model_name,
                COUNT(*) as total_operations,
                COUNT(CASE WHEN success_flag THEN 1 END) as successful_operations,
                AVG(CASE WHEN success_flag THEN latency_ms END) as avg_latency_ms,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms,
                AVG(CASE WHEN success_flag THEN input_tokens END) as avg_input_tokens,
                AVG(CASE WHEN success_flag THEN output_tokens END) as avg_output_tokens,
                SUM(CASE WHEN success_flag THEN cost_usd ELSE 0 END) as total_cost_usd,
                AVG(CASE WHEN success_flag THEN cost_usd END) as avg_cost_per_operation
            FROM {self.telemetry_table}
            WHERE timestamp >= DATEADD(HOUR, -{hours_back}, CURRENT_TIMESTAMP())
            GROUP BY operation_type, model_name
            ORDER BY total_operations DESC
            """
            
            results = self.session.sql(metrics_sql).collect()
            
            metrics = []
            for row in results:
                success_rate = (row['SUCCESSFUL_OPERATIONS'] / row['TOTAL_OPERATIONS']) if row['TOTAL_OPERATIONS'] > 0 else 0
                
                metrics.append({
                    'operation_type': row['OPERATION_TYPE'],
                    'model_name': row['MODEL_NAME'],
                    'total_operations': row['TOTAL_OPERATIONS'],
                    'success_rate': round(success_rate * 100, 2),
                    'avg_latency_ms': round(row['AVG_LATENCY_MS'] or 0, 2),
                    'p95_latency_ms': round(row['P95_LATENCY_MS'] or 0, 2),
                    'avg_input_tokens': round(row['AVG_INPUT_TOKENS'] or 0, 0),
                    'avg_output_tokens': round(row['AVG_OUTPUT_TOKENS'] or 0, 0),
                    'total_cost_usd': round(row['TOTAL_COST_USD'] or 0, 4),
                    'avg_cost_per_operation': round(row['AVG_COST_PER_OPERATION'] or 0, 6)
                })
            
            return {
                'time_window_hours': hours_back,
                'metrics_by_operation': metrics,
                'summary': self._calculate_summary_metrics(metrics)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    def _calculate_summary_metrics(self, metrics: list) -> Dict[str, Any]:
        """Calculate summary metrics across all operations"""
        if not metrics:
            return {}
        
        total_ops = sum(m['total_operations'] for m in metrics)
        total_cost = sum(m['total_cost_usd'] for m in metrics)
        
        # Weighted averages
        weighted_success_rate = sum(m['success_rate'] * m['total_operations'] for m in metrics) / total_ops if total_ops > 0 else 0
        weighted_avg_latency = sum(m['avg_latency_ms'] * m['total_operations'] for m in metrics) / total_ops if total_ops > 0 else 0
        
        return {
            'total_operations': total_ops,
            'overall_success_rate': round(weighted_success_rate, 2),
            'average_latency_ms': round(weighted_avg_latency, 2),
            'total_cost_usd': round(total_cost, 4),
            'cost_per_operation': round(total_cost / total_ops, 6) if total_ops > 0 else 0
        }
    
    def get_error_analysis(self, hours_back: int = 24) -> Dict[str, Any]:
        """Analyze errors and failure patterns"""
        try:
            error_sql = f"""
            SELECT 
                operation_type,
                model_name,
                error_message,
                COUNT(*) as error_count,
                MIN(timestamp) as first_occurrence,
                MAX(timestamp) as last_occurrence
            FROM {self.telemetry_table}
            WHERE success_flag = FALSE
                AND timestamp >= DATEADD(HOUR, -{hours_back}, CURRENT_TIMESTAMP())
                AND error_message IS NOT NULL
            GROUP BY operation_type, model_name, error_message
            ORDER BY error_count DESC
            """
            
            results = self.session.sql(error_sql).collect()
            
            errors = []
            for row in results:
                errors.append({
                    'operation_type': row['OPERATION_TYPE'],
                    'model_name': row['MODEL_NAME'],
                    'error_message': row['ERROR_MESSAGE'],
                    'error_count': row['ERROR_COUNT'],
                    'first_occurrence': row['FIRST_OCCURRENCE'],
                    'last_occurrence': row['LAST_OCCURRENCE']
                })
            
            return {
                'time_window_hours': hours_back,
                'total_errors': sum(e['error_count'] for e in errors),
                'unique_error_types': len(errors),
                'error_details': errors[:10]  # Top 10 errors
            }
            
        except Exception as e:
            logger.error(f"Error analyzing errors: {e}")
            return {}
    
    def get_cost_breakdown(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get detailed cost breakdown by operation and model"""
        try:
            cost_sql = f"""
            SELECT 
                operation_type,
                model_name,
                SUM(CASE WHEN success_flag THEN cost_usd ELSE 0 END) as total_cost,
                COUNT(CASE WHEN success_flag THEN 1 END) as successful_ops,
                SUM(CASE WHEN success_flag THEN input_tokens ELSE 0 END) as total_input_tokens,
                SUM(CASE WHEN success_flag THEN output_tokens ELSE 0 END) as total_output_tokens,
                AVG(CASE WHEN success_flag THEN cost_usd END) as avg_cost_per_op
            FROM {self.telemetry_table}
            WHERE timestamp >= DATEADD(HOUR, -{hours_back}, CURRENT_TIMESTAMP())
            GROUP BY operation_type, model_name
            HAVING total_cost > 0
            ORDER BY total_cost DESC
            """
            
            results = self.session.sql(cost_sql).collect()
            
            cost_breakdown = []
            total_cost = 0
            
            for row in results:
                cost = row['TOTAL_COST']
                total_cost += cost
                
                cost_breakdown.append({
                    'operation_type': row['OPERATION_TYPE'],
                    'model_name': row['MODEL_NAME'],
                    'total_cost_usd': round(cost, 4),
                    'successful_operations': row['SUCCESSFUL_OPS'],
                    'total_input_tokens': row['TOTAL_INPUT_TOKENS'],
                    'total_output_tokens': row['TOTAL_OUTPUT_TOKENS'],
                    'avg_cost_per_operation': round(row['AVG_COST_PER_OP'] or 0, 6),
                    'cost_percentage': 0  # Will be calculated below
                })
            
            # Calculate cost percentages
            for item in cost_breakdown:
                if total_cost > 0:
                    item['cost_percentage'] = round((item['total_cost_usd'] / total_cost) * 100, 2)
            
            return {
                'time_window_hours': hours_back,
                'total_cost_usd': round(total_cost, 4),
                'cost_by_operation': cost_breakdown
            }
            
        except Exception as e:
            logger.error(f"Error getting cost breakdown: {e}")
            return {}
    
    def cleanup_old_records(self, days_to_keep: int = 90):
        """Clean up old telemetry records"""
        try:
            cleanup_sql = f"""
            DELETE FROM {self.telemetry_table}
            WHERE timestamp < DATEADD(DAY, -{days_to_keep}, CURRENT_TIMESTAMP())
            """
            
            result = self.session.sql(cleanup_sql).collect()
            deleted_count = result[0]['number of rows deleted'] if result else 0
            
            logger.info(f"Cleaned up {deleted_count} old telemetry records (>{days_to_keep} days)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up telemetry records: {e}")
            return 0


class OperationTracker:
    """Context manager for automatic operation tracking"""
    
    def __init__(self, telemetry_tracker: TelemetryTracker, operation_type: str, model_name: str = None):
        self.tracker = telemetry_tracker
        self.operation_type = operation_type
        self.model_name = model_name
        self.start_time = None
        self.telemetry_id = None
        self.input_tokens = 0
        self.output_tokens = 0
        self.query_text = None
        self.response_text = None
        self.metadata = {}
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self.start_time) * 1000
        success_flag = exc_type is None
        error_message = str(exc_val) if exc_val else None
        
        # Calculate cost if tokens are available
        total_tokens = self.input_tokens + self.output_tokens
        cost_usd = calculate_token_cost(total_tokens, self.model_name) if self.model_name and total_tokens > 0 else 0.0
        
        self.telemetry_id = self.tracker.log_operation(
            operation_type=self.operation_type,
            model_name=self.model_name,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            success_flag=success_flag,
            error_message=error_message,
            query_text=self.query_text,
            response_text=self.response_text,
            metadata=self.metadata
        )
    
    def set_tokens(self, input_tokens: int = 0, output_tokens: int = 0):
        """Set token counts for cost calculation"""
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
    
    def set_query(self, query_text: str):
        """Set query text for logging"""
        self.query_text = query_text
    
    def set_response(self, response_text: str):
        """Set response text for logging"""
        self.response_text = response_text
    
    def add_metadata(self, **kwargs):
        """Add metadata to the operation"""
        self.metadata.update(kwargs)


def main():
    """Main function for testing and CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Snowflake GenAI Telemetry Tracker')
    parser.add_argument('--setup', action='store_true', help='Setup telemetry table')
    parser.add_argument('--metrics', type=int, default=24, help='Get performance metrics for last N hours')
    parser.add_argument('--errors', type=int, default=24, help='Analyze errors for last N hours')
    parser.add_argument('--costs', type=int, default=24, help='Get cost breakdown for last N hours')
    parser.add_argument('--cleanup', type=int, help='Clean up records older than N days')
    
    args = parser.parse_args()
    
    try:
        tracker = TelemetryTracker()
        
        if args.setup:
            print("Setting up telemetry table...")
            tracker.setup_telemetry_table()
            print("Telemetry table setup complete!")
        
        if args.metrics:
            print(f"Performance Metrics (last {args.metrics} hours):")
            metrics = tracker.get_performance_metrics(args.metrics)
            if metrics.get('summary'):
                summary = metrics['summary']
                print(f"  Total Operations: {summary['total_operations']}")
                print(f"  Success Rate: {summary['overall_success_rate']}%")
                print(f"  Average Latency: {summary['average_latency_ms']}ms")
                print(f"  Total Cost: ${summary['total_cost_usd']}")
        
        if args.errors:
            print(f"Error Analysis (last {args.errors} hours):")
            errors = tracker.get_error_analysis(args.errors)
            print(f"  Total Errors: {errors.get('total_errors', 0)}")
            print(f"  Unique Error Types: {errors.get('unique_error_types', 0)}")
        
        if args.costs:
            print(f"Cost Breakdown (last {args.costs} hours):")
            costs = tracker.get_cost_breakdown(args.costs)
            print(f"  Total Cost: ${costs.get('total_cost_usd', 0)}")
            for item in costs.get('cost_by_operation', [])[:5]:
                print(f"  {item['operation_type']}: ${item['total_cost_usd']} ({item['cost_percentage']}%)")
        
        if args.cleanup:
            print(f"Cleaning up records older than {args.cleanup} days...")
            deleted = tracker.cleanup_old_records(args.cleanup)
            print(f"Deleted {deleted} old records")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()