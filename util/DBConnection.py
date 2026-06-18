import mysql.connector
from mysql.connector import Error

def getConnection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="coralkita_v3"
    )

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

if __name__ == "__main__":
    test_connection()