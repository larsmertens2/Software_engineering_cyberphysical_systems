import os
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from flask_socketio import SocketIO, emit
import json

app = Flask(__name__)
CORS(app) 
socketio = SocketIO(app, cors_allowed_origins="*")

locked_aisles = {}

def resolve_map_file_path():
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "controllers", "robot_controller", "map.json"),
        os.path.join(os.path.dirname(__file__), "controllers", "robot_controller", "map.json"),
        "/app/controllers/robot_controller/map.json",
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return candidates[0]

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
            print(f"connection {i+1} failed: {err}")
            time.sleep(2)
    return None


@app.route('/api/items', methods=['GET']) #inventory for frontend
def get_items():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(items)


@app.route('/api/queue', methods=['POST']) #add new item to qeue
def add_to_queue():
    data = request.json
    item_id = data.get('item_id')
    
    if not item_id:
        return jsonify({"error": "item_id is mandatory"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO job_queue (item_id, status) VALUES (%s, 'pending')", (item_id,))
    conn.commit()
    cursor.close()
    conn.close()
    socketio.emit('queue_updated', {'message': 'New task added'})
    return jsonify({"message": "Task added to qeue"}), 201


@app.route('/api/queue/claim', methods=['POST'])#robot claims task
def claim_batch():
    data = request.json
    robot_id = data.get('robot_id')
    batch_size = data.get('batch_size', 3) 
    
    if not robot_id:
        return jsonify({"error": "robot_id is mandatory"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "database not reachable"}), 503

    cursor = conn.cursor(dictionary=True)

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

    task_ids = [t['id'] for t in tasks]
    format_strings = ','.join(['%s'] * len(task_ids))
    update_query = f"UPDATE job_queue SET status = 'assigned', robot_id = %s WHERE id IN ({format_strings})"
    
    cursor.execute(update_query, (robot_id, *task_ids))
    conn.commit()
    
    socketio.emit('queue_updated', {'message': 'Task assigned'})

    cursor.close()
    conn.close()
    
    return jsonify(tasks)

@app.route('/api/queue/complete', methods=['POST']) # task completed
def complete_task():
    data = request.json
    task_id = data.get('task_id')
    
    if not task_id:
        return jsonify({"error": "task_id is mandatory"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "database not reachable"}), 503

    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT item_id FROM job_queue WHERE id = %s", (task_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "Task not found"}), 404
        
        item_id = result[0]
        cursor.execute("UPDATE job_queue SET status = 'completed' WHERE id = %s", (task_id,))

        cursor.execute("UPDATE items SET stock = stock - 1 WHERE id = %s AND stock > 0", (item_id,))

        conn.commit()
        
        socketio.emit('queue_updated', {'message': 'Task completed'})
        socketio.emit('inventory_updated', {'message': 'Iventory changed'})


        return jsonify({
            "message": f"Task {task_id} completed and inventory updated",
            "item_id": item_id
        }), 200

    except mysql.connector.Error as err:
        conn.rollback() 
        return jsonify({"error": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/queue/aisle/lock', methods=['POST'])
def lock_aisle():
    data = request.json
    robot_id = data.get("robot_id")
    target_node = data.get("aisle")  # Bijv. 'Ailse_2' of 'Ailse_2_A'
    
    # We pakken de basisnaam van de gang (zodat we de HELE gang locken)
    # "Ailse_2_A" wordt "Ailse_2". "Ailse_3" blijft gewoon "Ailse_3".
    parts = target_node.split('_')
    if len(parts) >= 2:
        base_aisle = f"{parts[0]}_{parts[1]}"
    else:
        base_aisle = target_node

    # 1. Check of de gang AL bezet is
    if base_aisle in locked_aisles:
        # Is hij bezet door DEZE robot? -> Laat hem door! (Hij verplaatst zich binnen de gang)
        if locked_aisles[base_aisle] == robot_id:
            print(f"[API] Status: {robot_id} navigeert verder binnen {base_aisle}.")
            return jsonify({"success": True})
            
        # Is hij bezet door een ANDERE robot? -> Tegenhouden!
        else:
            print(f"[API] Status: GEWEIGERD! {robot_id} wil in {base_aisle}, maar deze is GELOCKED door {locked_aisles[base_aisle]}.")
            return jsonify({"success": False})

    # 2. De gang is vrij! We geven deze robot toegang.
    locked_aisles[base_aisle] = robot_id
    print(f"[API] Status: {base_aisle} is nu succesvol GELOCKED door {robot_id}!")
    return jsonify({"success": True})

@app.route('/api/queue/aisle/unlock', methods=['POST'])
def unlock_aisle():
    data = request.json
    robot_id = data.get('robot_id')
    
    unlocked_list = []
    # Zoek alle gangen die door deze robot bezet zijn en geef ze vrij
    # We gebruiken list(locked_aisles.items()) om de dictionary veilig aan te passen tijdens de loop
    for aisle, bot in list(locked_aisles.items()):
        if bot == robot_id:
            del locked_aisles[aisle]
            unlocked_list.append(aisle)
            print(f"[API] {aisle} is VRIJGEGEVEN door {robot_id}")
            
    return jsonify({"success": True, "unlocked": unlocked_list}), 200

@app.route('/api/queue/aisle/reset_all', methods=['POST', 'GET'])
def reset_all_aisles():
    # Maak de hele dictionary met gelockte gangen leeg
    locked_aisles.clear()
    print("[API] Alle gangen zijn geforceerd vrijgegeven (RESET)!")
    return jsonify({"success": True, "message": "Alle locks verwijderd"})

@app.route('/api/queue/status', methods=['GET'])
def get_queue_status():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
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


@app.route('/api/map', methods=['GET'])
def get_map():
    file_path = resolve_map_file_path()

    try:
        if not os.path.exists(file_path):
            return jsonify({"error": f"Bestand niet gevonden op {file_path}"}), 404

        with open(file_path, encoding='utf-8') as file_handle:
            return jsonify(json.load(file_handle))
    except Exception as error:
        return jsonify({"error": str(error)}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True,  allow_unsafe_werkzeug=True)