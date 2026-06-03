import os
import mysql.connector
from mysql.connector import Error

def getConnection():
    """Get database connection for CoralKita - Works locally and on Kerocket"""
    
    # Check if running on Kerocket (DATABASE_URL is provided)
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Parse DATABASE_URL from Kerocket
        # Format: mysql://username:password@host:port/database
        import re
        pattern = r'mysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, database_url)
        
        if match:
            username = match.group(1)
            password = match.group(2)
            host = match.group(3)
            port = match.group(4)
            database = match.group(5)
            
            return mysql.connector.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                database=database
            )
    
    # Local development (your existing code)
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="coralkita_v3",
    )


# Optional: Test connection function
def test_connection():
    """Test if database connection works"""
    try:
        conn = getConnection()
        if conn.is_connected():
            print("Connected to CoralKita database")
            return True
        else:
            print("Failed to connect to database")
            return False
    except Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()


# Auto-test when script runs directly
if __name__ == "__main__":
    test_connection()