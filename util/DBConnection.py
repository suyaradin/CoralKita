import mysql.connector;

def getConnection():
    """Get database connection for CoralKita"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="coralkita_v3",
    )

if getConnection().is_connected():
    print("Connected to CoralKita database")
else:
    print("Failed to connect to database")

getConnection().close()