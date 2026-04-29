import requests

class TaskManager:
    def __init__(self, robot_id):
        self.base_url = "http://127.0.0.1:5000/api/queue"
        self.robot_id = robot_id
        self.api_ip = "localhost"

        dropoff_map = {
        "Bot_1": "Droppoff_1",
        "Bot_2": "Droppoff_2",
        "Bot_3": "Droppoff_3",
        }     
        self.dropoff_point = dropoff_map.get(robot_id) 
        
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
                    
                    formatted_tasks.append([pickup_node, self.dropoff_point, t.get('id')])
                
                return formatted_tasks
            else:
                print(f"Claim failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"could not connect to flask: {e}")
        return []

    def complete_task(self, task_id):
        """tall flask api task is done"""
        if task_id is None:
            return
        try:
            response = requests.post(f"{self.base_url}/complete", json={"task_id": task_id}, timeout=5)
            if response.status_code == 200:
                print(f"task {task_id} deleted from database")
            else:
                print(f"could not complete task {task_id}: {response.text}")
        except Exception as e:
            print(f"error when complete_task: {e}")
