import mysql.connector
import os

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Vikas@2005",
    "database": "learnifydb",
}

def get_db():
    """Returns a fresh MySQL connection. Caller is responsible for closing it."""
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn
