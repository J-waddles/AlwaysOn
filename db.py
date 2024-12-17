import mysql.connector
from mysql.connector import Error
import json
import os


def create_db_connection():
    if os.getenv("TOKEN"):
        try:
            mydb = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST"),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                database=os.getenv("MYSQL_DB"),
                port=os.getenv("PORT"),
                autocommit=True,
                use_pure=True
            )
            return mydb
        except Error as err:
            print(f"Database connection failed due to: {err}")
            return None
    else: 
         # Load the config file for Test Bot
        with open('config.json', 'r') as f:
            config = json.load(f)
        try:
            mydb = mysql.connector.connect(
                host=config["MYSQL_HOST"],
                user=config["MYSQL_USER"],
                password=config["MYSQL_PASSWORD"],
                database=config["MYSQL_DB"],
                port=config["PORT"]
            )
            print("Database connected successfully.")
            return mydb
        except Error as err:
            print(f"Error connecting to the database: {err}")
            return None
        

def initialize_tables(connection):
    cursor = connection.cursor()
    # Example table initialization
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                server_id BIGINT PRIMARY KEY,
                server_name VARCHAR(255),
                active BOOLEAN DEFAULT TRUE
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                channel_id BIGINT PRIMARY KEY,
                server_id BIGINT,
                channel_name VARCHAR(255),
                category_name VARCHAR(255),
                user_pair_count INT DEFAULT 0,
                FOREIGN KEY (server_id) REFERENCES servers(server_id) ON DELETE CASCADE
            );
        """)
        connection.commit()
        print("Database tables initialized.")
    except Error as e:
        print(f"Error initializing tables: {e}")