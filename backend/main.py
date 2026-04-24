import os
from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app) 

def get_db_connection():
    return mysql.connector.connect(
        # Gebruik de environment variabele of val terug op 'db' (Docker naam)
        host=os.getenv('DB_HOST', 'db'), 
        user=os.getenv('DB_USER', 'secs'),
        password=os.getenv('DB_PASSWORD', 'secs'),
        database=os.getenv('DB_NAME', 'warehouse')
    )

@app.route('/api/items', methods=['GET'])
def get_items():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(items)

if __name__ == '__main__':
    # Verander NIET de poort, maar wel de host naar 0.0.0.0
    app.run(host='0.0.0.0', port=5000, debug=True)