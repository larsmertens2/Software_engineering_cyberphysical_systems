import os
import time
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from flask_socketio import SocketIO, emit
import json

app = Flask(__name__)
CORS(app) 
socketio = SocketIO(app, cors_allowed_origins="*")

locked_nodes = {}
locked_aisles = {}

# Wordt bijgehouden door aisle devices (via POST /api/aisle/state)
# { "Aisle_1": { "locked_by": "Bot_1" | None, "waiting": [{"robot_id": "Bot_2", "node": "A3"}] } }
aisle_states = {}

# Emergency stop state
emergency_active = False

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


@app.route('/api/queue/claim', methods=['POST'])
def claim_batch():
    data = request.json
    robot_id = data.get('robot_id')

    if not robot_id:
        return jsonify({"error": "robot_id is mandatory"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "database not reachable"}), 503

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT q.id, i.aisle
            FROM job_queue q
            JOIN items i ON q.item_id = i.id
            WHERE q.status = 'assigned' AND q.robot_id = %s
            LIMIT 1
        """, (robot_id,))
        assigned = cursor.fetchone()
        
        if assigned:
            return jsonify([assigned]), 200

        cursor.execute("""
            UPDATE job_queue 
            SET status = 'assigned', robot_id = %s 
            WHERE status = 'pending' 
            ORDER BY id ASC 
            LIMIT 1
        """, (robot_id,))
        conn.commit()

        if cursor.rowcount > 0:
            cursor.execute("""
                SELECT q.id, i.aisle
                FROM job_queue q
                JOIN items i ON q.item_id = i.id
                WHERE q.status = 'assigned' AND q.robot_id = %s
            """, (robot_id,))
            new_task = cursor.fetchone()
            
            socketio.emit('queue_updated', {'message': 'Task assigned'})
            return jsonify([new_task]), 200
        
        # Geen taken beschikbaar
        return jsonify([]), 200

    except Exception as e:
        print(f"Fout in claim_batch: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

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

@app.route('/api/aisle/state', methods=['POST'])
def update_aisle_state():
    data = request.json
    aisle = data.get('aisle_id')
    if not aisle:
        return jsonify({"error": "aisle_id is mandatory"}), 400

    aisle_states[aisle] = {
        "locker": data.get("locker"),
        "waiting": data.get("waiting", []),
    }
    print(f"[AISLE] {aisle}: locker={aisle_states[aisle]['locker']}, waiting={aisle_states[aisle]['waiting']}")
    socketio.emit('aisle_updated', aisle_states)
    return jsonify({"ok": True})

@app.route('/api/aisle/states', methods=['GET'])
def get_aisle_states():
    return jsonify(aisle_states)

# Emergency stop endpoints
@app.route('/api/emergency', methods=['GET'])
def get_emergency_status():
    """Get the current emergency status"""
    global emergency_active
    return jsonify({
        "emergency_active": emergency_active
    }), 200

@app.route('/api/emergency', methods=['POST'])
def toggle_emergency():
    """Toggle emergency state"""
    global emergency_active
    emergency_active = not emergency_active
    
    print(f"[EMERGENCY] Emergency status toggled to: {emergency_active}")
    
    # Broadcast to all connected clients
    socketio.emit('emergency_updated', {
        'emergency_active': emergency_active,
        'timestamp': time.time()
    })
    
    return jsonify({
        "emergency_active": emergency_active,
        "message": "EMERGENCY ACTIVATED" if emergency_active else "Emergency cleared"
    }), 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True,  allow_unsafe_werkzeug=True)