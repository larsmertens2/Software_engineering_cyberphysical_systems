import os
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app) 

def get_db_connection():
    for i in range(5):
        try:
            conn = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'db'), 
                user=os.getenv('DB_USER', 'secs'),
                password=os.getenv('DB_PASSWORD', 'secs'),
                database=os.getenv('DB_NAME', 'warehouse'),
                auth_plugin='mysql_native_password'
            )
            return conn
        except mysql.connector.Error as err:
            print(f"Verbindingspoging {i+1} mislukt: {err}")
            time.sleep(2)
    return None


@app.route('/api/items', methods=['GET']) #inventory voor frontend
def get_items():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(items)


@app.route('/api/queue', methods=['POST']) #voeg nieuw item toe aan qeue
def add_to_queue():
    data = request.json
    item_id = data.get('item_id')
    
    if not item_id:
        return jsonify({"error": "item_id is verplicht"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO job_queue (item_id, status) VALUES (%s, 'pending')", (item_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Taak toegevoegd aan wachtrij"}), 201


@app.route('/api/queue/claim', methods=['POST'])#robot kan taken claimen
def claim_batch():
    data = request.json
    robot_id = data.get('robot_id')
    batch_size = data.get('batch_size', 3) 
    
    if not robot_id:
        return jsonify({"error": "robot_id is verplicht"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "database niet bereikbaar"}), 503

    cursor = conn.cursor(dictionary=True)

    # Geef eerst bestaande taken terug die al aan deze robot toegewezen zijn.
    assigned_query = """
        SELECT q.id, i.aisle
        FROM job_queue q
        JOIN items i ON q.item_id = i.id
        WHERE q.status = 'assigned' AND q.robot_id = %s
        ORDER BY q.id ASC
        LIMIT %s
    """
    cursor.execute(assigned_query, (robot_id, batch_size))
    assigned_tasks = cursor.fetchall()

    if assigned_tasks:
        cursor.close()
        conn.close()
        return jsonify(assigned_tasks), 200
    
    # Haal de oudste 'pending' taken op inclusief locatie info van de items tabel
    query = """
        SELECT q.id, i.aisle 
        FROM job_queue q
        JOIN items i ON q.item_id = i.id
        WHERE q.status = 'pending'
        ORDER BY q.id ASC
        LIMIT %s
    """
    cursor.execute(query, (batch_size,))
    tasks = cursor.fetchall()

    if not tasks:
        cursor.close()
        conn.close()
        return jsonify([]), 200

    # Update de status van deze specifieke taken naar 'assigned'
    task_ids = [t['id'] for t in tasks]
    format_strings = ','.join(['%s'] * len(task_ids))
    update_query = f"UPDATE job_queue SET status = 'assigned', robot_id = %s WHERE id IN ({format_strings})"
    
    cursor.execute(update_query, (robot_id, *task_ids))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    # Robot krijgt ID's en locatie (node)
    return jsonify(tasks)

@app.route('/api/queue/complete', methods=['POST']) #task is complete
def complete_task():
    data = request.json
    task_id = data.get('task_id')
    
    if not task_id:
        return jsonify({"error": "task_id is verplicht"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE job_queue SET status = 'completed' WHERE id = %s", (task_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": f"Taak {task_id} voltooid"}), 200

# 4. Voor het Dashboard: Monitor de huidige status van de wachtrij
@app.route('/api/queue/status', methods=['GET'])
def get_queue_status():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Haal alle niet-voltooide taken op voor de monitoring
    query = """
        SELECT q.id, q.status, q.robot_id, q.created_at, i.name, i.aisle
        FROM job_queue q
        JOIN items i ON q.item_id = i.id
        WHERE q.status != 'completed'
        ORDER BY q.created_at ASC
    """
    cursor.execute(query)
    status_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(status_list)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)