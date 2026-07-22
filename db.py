import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()["count"]

    if count == 0:
        seed_tasks = [
            ("Learn FastAPI", False),
            ("Build a CRUD API", False),
            ("Test the API with Swagger", True),
        ]
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
            seed_tasks
        )

    conn.commit()
    cursor.close()
    conn.close()

def row_to_task(row):
    return {"id": row["id"], "title": row["title"], "done": row["done"]}