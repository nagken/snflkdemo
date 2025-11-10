"""
Snowflake Connection Test
Run this to verify your Snowflake credentials and Cortex access
"""

import os
import sys
from dotenv import load_dotenv

def test_connection():
    """Test Snowflake connection and Cortex availability"""
    print("🔍 Testing Snowflake Connection...")
    
    # Load environment variables
    load_dotenv('config/.env')
    
    # Check if credentials are provided
    required_vars = [
        'SNOWFLAKE_ACCOUNT',
        'SNOWFLAKE_USER', 
        'SNOWFLAKE_PASSWORD',
        'SNOWFLAKE_WAREHOUSE',
        'SNOWFLAKE_DATABASE',
        'SNOWFLAKE_SCHEMA'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_'):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing Snowflake credentials!")
        print("\nPlease update config/.env with your Snowflake details:")
        for var in missing_vars:
            print(f"  • {var}")
        print("\n📋 To get your Snowflake credentials:")
        print("  1. Log into your Snowflake account")
        print("  2. Note your account identifier from the URL")
        print("  3. Ensure you have USAGE privilege on Cortex functions")
        print("  4. Update config/.env with your actual values")
        return False
    
    try:
        import snowflake.connector
        
        # Create connection
        conn = snowflake.connector.connect(
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA')
        )
        
        print("✅ Connection successful!")
        
        # Test Cortex access
        cursor = conn.cursor()
        
        # Test EMBED_TEXT_768
        try:
            cursor.execute("SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768('text-embedding-ada-002', 'test')")
            print("✅ CORTEX.EMBED_TEXT_768 available")
        except Exception as e:
            print(f"❌ CORTEX.EMBED_TEXT_768 not available: {e}")
            
        # Test COMPLETE
        try:
            cursor.execute("SELECT SNOWFLAKE.CORTEX.COMPLETE('llama2-7b-chat', 'Hello')")
            print("✅ CORTEX.COMPLETE available")
        except Exception as e:
            print(f"❌ CORTEX.COMPLETE not available: {e}")
            
        cursor.close()
        conn.close()
        
        print("\n🎉 Ready to run the full pipeline!")
        print("\nNext steps:")
        print("  1. python3 src/ingest_loader.py")
        print("  2. python3 src/embed_generator.py") 
        print("  3. python3 src/cortex_query.py")
        print("  4. python3 -m streamlit run src/dashboard_plot.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("  • Check your account identifier (should not include .snowflakecomputing.com)")
        print("  • Verify username/password are correct")
        print("  • Ensure warehouse/database/schema exist and you have access")
        print("  • Confirm Cortex functions are enabled in your account")
        return False

if __name__ == "__main__":
    success = test_connection()
    if not success:
        print("\n🔧 For now, you can use the demo mode:")
        print("  python3 test_pipeline_demo.py")
    sys.exit(0 if success else 1)