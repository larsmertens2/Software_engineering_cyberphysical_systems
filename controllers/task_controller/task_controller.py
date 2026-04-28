import requests

class TaskManager:
    def __init__(self, robot_id):
        self.base_url = "http://localhost:5000/api/queue"
        self.robot_id = robot_id

        # Zorg dat de spelling van de droppoff exact overeenkomt met je map.json!
        dropoff_map = {
        "Bot_1": "Droppoff_1",
        "Bot_2": "Droppoff_2",
        "Bot_3": "Droppoff_3",
        }     
        self.dropoff_point = dropoff_map.get(robot_id, "Droppoff_2") 
        
        self.aisle_to_entrance = {
            1: "Entrance_1_3", 3: "Entrance_1_3",
            2: "Entrance_2_4", 4: "Entrance_2_4",
            5: "Entrance_5_7", 7: "Entrance_5_7",
            6: "Entrance_6_8", 8: "Entrance_6_8"
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
                    pickup_node = self.aisle_to_entrance.get(aisle_num, "Entrance_1_3")
                    
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