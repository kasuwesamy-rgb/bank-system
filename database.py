import os
import mysql.connector


def connect_db():

    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "bank_system"),
        port=int(os.getenv("DB_PORT", "3306"))
    )