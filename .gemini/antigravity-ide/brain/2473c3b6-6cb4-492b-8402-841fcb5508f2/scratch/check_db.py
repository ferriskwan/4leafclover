import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_PUBLIC_IP'),
    port=int(os.getenv('DB_PORT', '5432')),
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    sslmode='require'
)
cur = conn.cursor()
cur.execute("""
    SELECT table_name, column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name in ('tickdata', 'eoddata')
""")
for r in cur.fetchall():
    print(r)
