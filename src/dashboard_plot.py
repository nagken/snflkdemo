"""
Streamlit Dashboard for Snowflake Cortex GenAI Pipeline
Interactive dashboard for telemetry visualization and query testing.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

# Configure page
st.set_page_config(
    page_title="Cortex GenAI Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import our modules (with error handling for demo purposes)
try:
    from utils import get_session, load_settings, setup_logging
    from cortex_query import CortexQueryEngine
    from telemetry_task import TelemetryTracker
    from embed_generator import EmbeddingGenerator
    from ingest_loader import DocumentIngestor
    
    logger = setup_logging()
    MODULES_AVAILABLE = True
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.info("Please ensure all dependencies are installed and Snowflake connection is configured.")
    MODULES_AVAILABLE = False
    logger = logging.getLogger(__name__)


# Custom CSS for better styling
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    margin: 0.5rem 0;
}

.success-metric {
    background: linear-gradient(90deg, #56ab2f 0%, #a8e6cf 100%);
}

.warning-metric {
    background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
}

.info-metric {
    background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
}

.stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
    font-size: 1.1rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_telemetry_data(hours_back: int = 24):
    """Load telemetry data with caching"""
    if not MODULES_AVAILABLE:
        return None
    
    try:
        tracker = TelemetryTracker()
        
        # Get performance metrics
        metrics = tracker.get_performance_metrics(hours_back)
        errors = tracker.get_error_analysis(hours_back)
        costs = tracker.get_cost_breakdown(hours_back)
        
        return {
            'metrics': metrics,
            'errors': errors,
            'costs': costs,
            'timestamp': datetime.now()
        }
    except Exception as e:
        st.error(f"Error loading telemetry data: {e}")
        return None


@st.cache_data(ttl=600)  # Cache for 10 minutes
def load_document_stats():
    """Load document statistics with caching"""
    if not MODULES_AVAILABLE:
        return None
    
    try:
        ingestor = DocumentIngestor()
        doc_stats = ingestor.get_document_stats()
        
        generator = EmbeddingGenerator()
        embedding_stats = generator.get_embedding_stats()
        
        return {
            'documents': doc_stats,
            'embeddings': embedding_stats,
            'timestamp': datetime.now()
        }
    except Exception as e:
        st.error(f"Error loading document stats: {e}")
        return None


def create_metrics_cards(data: Dict[str, Any]):
    """Create metric cards for dashboard"""
    if not data or 'metrics' not in data:
        return
    
    summary = data['metrics'].get('summary', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            f"""<div class="metric-card success-metric">
            <h3>Total Operations</h3>
            <h2>{summary.get('total_operations', 0):,}</h2>
            </div>""", 
            unsafe_allow_html=True
        )
    
    with col2:
        success_rate = summary.get('overall_success_rate', 0)
        card_class = "success-metric" if success_rate >= 95 else "warning-metric" if success_rate >= 85 else "metric-card"
        st.markdown(
            f"""<div class="metric-card {card_class}">
            <h3>Success Rate</h3>
            <h2>{success_rate:.1f}%</h2>
            </div>""", 
            unsafe_allow_html=True
        )
    
    with col3:
        latency = summary.get('average_latency_ms', 0)
        card_class = "success-metric" if latency <= 2000 else "warning-metric" if latency <= 5000 else "metric-card"
        st.markdown(
            f"""<div class="metric-card {card_class}">
            <h3>⏱️ Avg Latency</h3>
            <h2>{latency:.0f}ms</h2>
            </div>""", 
            unsafe_allow_html=True
        )
    
    with col4:
        cost = summary.get('total_cost_usd', 0)
        st.markdown(
            f"""<div class="metric-card info-metric">
            <h3>💰 Total Cost</h3>
            <h2>${cost:.4f}</h2>
            </div>""", 
            unsafe_allow_html=True
        )


def create_performance_charts(data: Dict[str, Any]):
    """Create performance visualization charts"""
    if not data or 'metrics' not in data:
        return
    
    metrics_data = data['metrics'].get('metrics_by_operation', [])
    
    if not metrics_data:
        st.info("No performance data available for the selected time period.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(metrics_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Success Rate by Operation")
        
        # Success rate chart
        fig_success = px.bar(
            df, 
            x='operation_type', 
            y='success_rate',
            color='success_rate',
            color_continuous_scale='RdYlGn',
            title="Success Rate by Operation Type",
            labels={'success_rate': 'Success Rate (%)', 'operation_type': 'Operation Type'}
        )
        fig_success.update_layout(height=400, showlegend=False)
        fig_success.update_traces(text=df['success_rate'], texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_success, use_container_width=True)
    
    with col2:
        st.subheader("⚡ Average Latency")
        
        # Latency chart
        fig_latency = px.bar(
            df,
            x='operation_type',
            y='avg_latency_ms',
            color='avg_latency_ms',
            color_continuous_scale='Viridis_r',
            title="Average Latency by Operation",
            labels={'avg_latency_ms': 'Latency (ms)', 'operation_type': 'Operation Type'}
        )
        fig_latency.update_layout(height=400, showlegend=False)
        fig_latency.update_traces(text=df['avg_latency_ms'], texttemplate='%{text:.0f}ms', textposition='outside')
        st.plotly_chart(fig_latency, use_container_width=True)
    
    # Combined operations overview
    st.subheader("📈 Operations Overview")
    
    fig_combined = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Total Operations', 'Average Cost per Operation', 'Token Usage', 'P95 Latency'),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Total operations
    fig_combined.add_trace(
        go.Bar(x=df['operation_type'], y=df['total_operations'], name='Total Ops'),
        row=1, col=1
    )
    
    # Average cost
    fig_combined.add_trace(
        go.Bar(x=df['operation_type'], y=df['avg_cost_per_operation'], name='Avg Cost'),
        row=1, col=2
    )
    
    # Token usage (input + output)
    fig_combined.add_trace(
        go.Bar(x=df['operation_type'], y=df['avg_input_tokens'], name='Input Tokens'),
        row=2, col=1
    )
    
    # P95 latency
    fig_combined.add_trace(
        go.Bar(x=df['operation_type'], y=df['p95_latency_ms'], name='P95 Latency'),
        row=2, col=2
    )
    
    fig_combined.update_layout(height=600, showlegend=False, title_text="Detailed Performance Metrics")
    st.plotly_chart(fig_combined, use_container_width=True)


def create_cost_analysis(data: Dict[str, Any]):
    """Create cost analysis visualizations"""
    if not data or 'costs' not in data:
        return
    
    costs_data = data['costs'].get('cost_by_operation', [])
    
    if not costs_data:
        st.info("No cost data available for the selected time period.")
        return
    
    df_costs = pd.DataFrame(costs_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💸 Cost Distribution")
        
        # Pie chart for cost distribution
        fig_pie = px.pie(
            df_costs,
            values='total_cost_usd',
            names='operation_type',
            title="Cost Distribution by Operation Type",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("📊 Cost vs Operations")
        
        # Scatter plot: cost vs operations
        fig_scatter = px.scatter(
            df_costs,
            x='successful_operations',
            y='total_cost_usd',
            size='avg_cost_per_operation',
            color='operation_type',
            title="Cost vs Number of Operations",
            labels={'successful_operations': 'Successful Operations', 'total_cost_usd': 'Total Cost (USD)'},
            hover_data=['avg_cost_per_operation']
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Cost efficiency analysis
    st.subheader("💡 Cost Efficiency Analysis")
    
    # Add efficiency metric (operations per dollar)
    df_costs['operations_per_dollar'] = df_costs['successful_operations'] / df_costs['total_cost_usd'].replace(0, 1)
    
    fig_efficiency = px.bar(
        df_costs,
        x='operation_type',
        y='operations_per_dollar',
        color='operations_per_dollar',
        color_continuous_scale='Greens',
        title="Operations per Dollar (Efficiency)",
        labels={'operations_per_dollar': 'Operations per $1 USD', 'operation_type': 'Operation Type'}
    )
    fig_efficiency.update_traces(text=df_costs['operations_per_dollar'], texttemplate='%{text:.1f}', textposition='outside')
    st.plotly_chart(fig_efficiency, use_container_width=True)


def create_error_analysis(data: Dict[str, Any]):
    """Create error analysis section"""
    if not data or 'errors' not in data:
        return
    
    errors_data = data['errors']
    
    st.subheader("🚨 Error Analysis")
    
    if errors_data.get('total_errors', 0) == 0:
        st.success("🎉 No errors detected in the selected time period!")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Errors", errors_data.get('total_errors', 0))
    
    with col2:
        st.metric("Unique Error Types", errors_data.get('unique_error_types', 0))
    
    # Error details table
    error_details = errors_data.get('error_details', [])
    
    if error_details:
        st.subheader("Top Error Messages")
        
        error_df = pd.DataFrame(error_details)
        error_df['error_rate'] = (error_df['error_count'] / error_df['error_count'].sum()) * 100
        
        # Format the table
        display_df = error_df[['operation_type', 'model_name', 'error_message', 'error_count', 'error_rate']].copy()
        display_df['error_message'] = display_df['error_message'].str[:100] + '...'  # Truncate long messages
        
        st.dataframe(
            display_df,
            column_config={
                "operation_type": "Operation",
                "model_name": "Model", 
                "error_message": "Error Message",
                "error_count": st.column_config.NumberColumn("Count", format="%d"),
                "error_rate": st.column_config.ProgressColumn("Error Rate %", min_value=0, max_value=100)
            },
            use_container_width=True
        )


def create_query_interface():
    """Create interactive query interface"""
    st.subheader("🤖 Interactive Query Interface")
    
    if not MODULES_AVAILABLE:
        st.error("Query interface unavailable - modules not loaded properly.")
        return
    
    # Query configuration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        use_search = st.checkbox("Enable Semantic Search", value=True)
    
    with col2:
        top_k = st.slider("Search Results (Top K)", min_value=1, max_value=10, value=5)
    
    with col3:
        temperature = st.slider("LLM Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    
    # Query input
    query = st.text_area("Enter your query:", placeholder="What are the benefits of AI automation?", height=100)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        submit_query = st.button("🚀 Submit Query", type="primary")
    
    with col2:
        if st.button("💡 Get Suggestions"):
            if query.strip():
                try:
                    engine = CortexQueryEngine()
                    suggestions = engine.get_query_suggestions(query)
                    
                    if suggestions:
                        st.write("**Query Suggestions:**")
                        for i, suggestion in enumerate(suggestions, 1):
                            st.write(f"{i}. {suggestion}")
                    else:
                        st.info("No suggestions available.")
                except Exception as e:
                    st.error(f"Error getting suggestions: {e}")
    
    with col3:
        example_queries = st.selectbox(
            "Example Queries",
            ["", "What are the benefits of AI automation?", 
             "How does Snowflake Cortex work?", 
             "What is a good GenAI strategy?",
             "Explain vector embeddings"]
        )
        if example_queries:
            query = example_queries
    
    # Process query
    if submit_query and query.strip():
        with st.spinner("Processing your query..."):
            try:
                engine = CortexQueryEngine()
                
                start_time = time.time()
                result = engine.query_with_context(
                    query,
                    use_search=use_search,
                    top_k=top_k,
                    temperature=temperature
                )
                processing_time = time.time() - start_time
                
                # Display results
                st.success(f"Query processed in {processing_time:.2f} seconds")
                
                # Answer
                st.markdown("### 📝 Answer")
                st.write(result['answer'])
                
                # Metrics
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📊 Performance Metrics")
                    metrics = result['metrics']
                    
                    st.metric("Total Latency", f"{metrics['total_latency_ms']:.0f}ms")
                    st.metric("Input Tokens", metrics['input_tokens'])
                    st.metric("Output Tokens", metrics['output_tokens'])
                    st.metric("Total Cost", f"${result['cost_estimate']['total_usd']:.6f}")
                
                with col2:
                    st.markdown("### 🔍 Search Results")
                    if result['context_used'] and result['search_results']:
                        st.metric("Search Results", len(result['search_results']))
                        
                        # Show top search results
                        for i, search_result in enumerate(result['search_results'][:3], 1):
                            with st.expander(f"Result {i}: {search_result['filename']} (Score: {search_result['similarity_score']:.3f})"):
                                st.write(search_result['content_chunk'][:300] + "...")
                    else:
                        st.info("Semantic search not used for this query.")
                
            except Exception as e:
                st.error(f"Error processing query: {e}")
                logger.error(f"Query processing error: {e}")


def main():
    """Main dashboard function"""
    
    # Header
    st.title("🧠 Snowflake Cortex GenAI Analytics Dashboard")
    st.markdown("Real-time monitoring and interaction with your GenAI pipeline")
    
    # Sidebar controls
    st.sidebar.title("⚙️ Dashboard Controls")
    
    # Time range selector
    time_range = st.sidebar.selectbox(
        "📅 Time Range",
        ["Last 1 Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"],
        index=2
    )
    
    hours_map = {
        "Last 1 Hour": 1,
        "Last 6 Hours": 6, 
        "Last 24 Hours": 24,
        "Last 7 Days": 168
    }
    hours_back = hours_map[time_range]
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh (30s)", value=False)
    
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Module status
    st.sidebar.markdown("### 📊 System Status")
    if MODULES_AVAILABLE:
        st.sidebar.success("All modules loaded")
    else:
        st.sidebar.error("❌ Modules not available")
    
    # Load data
    if MODULES_AVAILABLE:
        with st.spinner("Loading telemetry data..."):
            telemetry_data = load_telemetry_data(hours_back)
            doc_stats = load_document_stats()
    else:
        telemetry_data = None
        doc_stats = None
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "📈 Performance", "💰 Cost Analysis", "🤖 Query Interface", "📚 Documents"])
    
    with tab1:
        st.header("📊 Dashboard Overview")
        
        if telemetry_data:
            create_metrics_cards(telemetry_data)
            
            # Recent activity
            st.subheader("🕒 Recent Activity Summary")
            summary = telemetry_data['metrics'].get('summary', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Time Period:** {time_range}")
                st.info(f"**Last Updated:** {telemetry_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                if summary.get('total_operations', 0) > 0:
                    avg_latency = summary.get('average_latency_ms', 0)
                    success_rate = summary.get('overall_success_rate', 0)
                    
                    if success_rate >= 97 and avg_latency <= 2000:
                        st.success("🎉 System performing excellently!")
                    elif success_rate >= 90 and avg_latency <= 5000:
                        st.warning("⚠️ System performance is acceptable")
                    else:
                        st.error("🚨 System performance needs attention")
                else:
                    st.info("No operations recorded in this time period")
            
            # Error analysis in overview
            create_error_analysis(telemetry_data)
        else:
            st.warning("No telemetry data available. Please ensure the system is running and processing queries.")
    
    with tab2:
        st.header("📈 Performance Analytics")
        
        if telemetry_data:
            create_performance_charts(telemetry_data)
        else:
            st.info("No performance data available.")
    
    with tab3:
        st.header("💰 Cost Analysis")
        
        if telemetry_data:
            create_cost_analysis(telemetry_data)
        else:
            st.info("No cost data available.")
    
    with tab4:
        st.header("🤖 Interactive Query Interface")
        create_query_interface()
    
    with tab5:
        st.header("📚 Document Management")
        
        if doc_stats:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📄 Document Statistics")
                docs = doc_stats['documents']
                
                st.metric("Total Documents", docs.get('total_documents', 0))
                st.metric("Unique File Types", docs.get('unique_file_types', 0))
                st.metric("Average Content Length", f"{docs.get('avg_content_length', 0):,.0f} chars")
                st.metric("Total Size", f"{docs.get('total_size_mb', 0):.2f} MB")
            
            with col2:
                st.subheader("🧠 Embedding Statistics")
                embeddings = doc_stats['embeddings']
                
                st.metric("Total Embeddings", embeddings.get('total_embeddings', 0))
                st.metric("Unique Documents", embeddings.get('unique_documents', 0))
                st.metric("Average Tokens per Chunk", f"{embeddings.get('avg_tokens_per_chunk', 0):.0f}")
                st.metric("Average Chunk Size", f"{embeddings.get('avg_chunk_size', 0):.0f} chars")
        else:
            st.info("No document statistics available.")
    
    # Footer
    st.markdown("---")
    st.markdown("💡 **Snowflake Cortex GenAI Pipeline Dashboard** - Built with Streamlit")


if __name__ == "__main__":
    main()