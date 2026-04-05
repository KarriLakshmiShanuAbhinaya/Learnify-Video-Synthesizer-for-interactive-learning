import MySQLdb
import os
from dotenv import load_dotenv

load_dotenv()

def create_feedback_table():
    try:
        # Using environment variables from .env if available, otherwise fallback to known defaults
        host = os.getenv("DB_HOST", "localhost")
        user = os.getenv("DB_USER", "root")
        passwd = os.getenv("DB_PASSWORD", "Vikas@2005")
        db_name = os.getenv("DB_NAME", "learnifydb")

        db = MySQLdb.connect(
            host=host,
            user=user,
            passwd=passwd,
            db=db_name
        )
        cur = db.cursor()
        
        # Create feedback table
        print(f"Connecting to {db_name} as {user}...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                username VARCHAR(100),
                content TEXT NOT NULL,
                rating INT DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        db.commit()
        print("✅ Table 'feedback' created successfully.")
        
        cur.close()
        db.close()
    except Exception as e:
        print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    create_feedback_table()
