import requests

class TaskManager:
    def __init__(self):
        # Let op: als je met Docker werkt, moet 'localhost' 
        # soms het IP van je host machine zijn, of '127.0.0.1'
        self.base_url = "http://localhost:5000/api/queue"
        self.robot_id = "bot_2" 
        self.dropoff_point = "Droppoff_2" # MOET matchen met map.json!

        self.aisle_to_entrance = {
            1: "Entrance_1_3", 3: "Entrance_1_3",
            2: "Entrance_2_4", 4: "Entrance_2_4",
            5: "Entrance_5_7", 7: "Entrance_5_7",
            6: "Entrance_6_8", 8: "Entrance_6_8"
        }

    def get_task_list(self, size):
        try:
            # We sturen robot_id en batch_size naar de Flask claim endpoint
            payload = {"robot_id": self.robot_id, "batch_size": size}
            response = requests.post(f"{self.base_url}/claim", json=payload, timeout=5)
            
            if response.status_code == 200:
                api_tasks = response.json()
                
                # Als de lijst leeg is, zijn er geen 'pending' taken
                if not api_tasks:
                    return []

                formatted_tasks = []
                for t in api_tasks:
                    # 'aisle' komt uit de JOIN in je Flask query
                    aisle_num = t.get('aisle')
                    pickup_node = self.aisle_to_entrance.get(aisle_num, "Entrance_1_3")
                    
                    # We geven [Pickup, Dropoff, Task_ID] terug
                    formatted_tasks.append([pickup_node, self.dropoff_point])
                
                #print(f"Robot {self.robot_id} heeft {len(formatted_tasks)} taken geclaimd.")
                return formatted_tasks
            else:
                print(f"Claim mislukt: HTTP {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Fout bij verbinden met Flask: {e}")
        return []