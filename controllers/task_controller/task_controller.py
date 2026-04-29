import requests

class TaskManager:
    def __init__(self, robot_id):
        self.base_url = "http://127.0.0.1:5000/api/queue"
        self.robot_id = robot_id
        self.api_ip = "localhost"

        # Zorg dat de spelling van de droppoff exact overeenkomt met je map.json!
        dropoff_map = {
        "Bot_1": "Droppoff_1",
        "Bot_2": "Droppoff_2",
        "Bot_3": "Droppoff_3",
        }     
        self.dropoff_point = dropoff_map.get(robot_id, "Droppoff_2") 
        
        self.aisle_to_entrance = {
            1: "Aisle_2_2", 3: "Aisle_2_2",
            2: "Aisle_1_2", 4: "Aisle_1_2",
            5: "Aisle_3_2", 7: "Aisle_3_2",
            6: "Aisle_4_2", 8: "Aisle_4_2"
        }

    def get_task_list(self, size):
        try:
            payload = {"robot_id": self.robot_id, "batch_size": size}
            response = requests.post(f"{self.base_url}/claim", json=payload, timeout=5)
            
            if response.status_code == 200:
                api_tasks = response.json()
                
                if not api_tasks:
                    return []

                formatted_tasks = []
                for t in api_tasks:
                    aisle_num = t.get('aisle')
                    pickup_node = self.aisle_to_entrance.get(aisle_num)
                    
                    # CRUCIAAL: Voeg t.get('id') toe zodat de robot weet welke taak hij doet
                    formatted_tasks.append([pickup_node, self.dropoff_point, t.get('id')])
                
                return formatted_tasks
            else:
                print(f"Claim mislukt: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"Fout bij verbinden met Flask: {e}")
        return []

    def complete_task(self, task_id):
        """Meldt bij de Flask API dat de taak klaar is"""
        if task_id is None:
            return
            
        try:
            # We sturen de task_id naar je Flask endpoint /api/queue/complete
            response = requests.post(f"{self.base_url}/complete", json={"task_id": task_id}, timeout=5)
            if response.status_code == 200:
                print(f"Taak {task_id} succesvol afgemeld in database.")
            else:
                print(f"Kon taak {task_id} niet voltooien: {response.text}")
        except Exception as e:
            print(f"Fout bij complete_task: {e}")
    
    def lock_aisle(self, aisle_name):
        try:
            payload = {"robot_id": self.robot_id, "aisle": aisle_name}
            request_url = f"{self.base_url}/aisle/lock" # We zetten de URL in een variabele
            
            print(f"[{self.robot_id}] POST naar: {request_url}") # Print de exacte URL!
            
            response = requests.post(request_url, json=payload, timeout=5)
            # ... de rest van je code ...
            if response.status_code == 200:
                return response.json().get("success", False)
        except Exception as e:
            print(f"[{self.robot_id}] CRASH bij bereiken API: {e}") # AANGEPAST
        return False

    def unlock_aisle(self):
        """Meldt aan de API dat de robot uit de gang is, zodat anderen erin mogen."""
        try:
            payload = {"robot_id": self.robot_id}
            requests.post(f"{self.base_url}/aisle/unlock", json=payload, timeout=5)
        except Exception as e:
            print(f"Fout bij API unlock_aisle: {e}")

    def reset_all_locks(self):
        try:
            url = f"{self.base_url}/aisle/reset_all"
            response = requests.post(url)
            if response.status_code == 200:
                print("Alle gelockte gangen zijn gereset in de API!")
        except Exception as e:
            print(f"Kon de API niet bereiken om te resetten: {e}")