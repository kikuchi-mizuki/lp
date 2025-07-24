import os
import sqlite3
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL', 'database.db')

def get_db_connection():
    if DATABASE_URL.startswith('postgresql://'):
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect(DATABASE_URL) 