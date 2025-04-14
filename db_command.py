
import os
import sys
import psycopg2
from urllib.parse import urlparse

def run_db_command(sql_command):
    """Run a SQL command using the DATABASE_URL environment variable."""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        cur.execute(sql_command)
        
        # Fetch and print results if any
        try:
            results = cur.fetchall()
            for row in results:
                print(row)
        except:
            # Not a SELECT query or no results
            pass
            
        print("Command executed successfully")
        
    except Exception as e:
        print(f"Error executing command: {str(e)}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python db_command.py \"SQL COMMAND\"")
    else:
        sql_command = sys.argv[1]
        run_db_command(sql_command)
