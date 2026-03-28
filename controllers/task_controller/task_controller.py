class TaskManager:
    def __init__(self):
        # Lijst met orders: (pickup_node, dropoff_node)
        self.queue = [
            # --- Sector: Diep Magazijn (Rij F en E) ---
            ("F1", "Droppoff_1"), # Van linksachter naar links-dropoff
            ("F2", "Droppoff_3"), # Van rechtsachter naar rechts-dropoff
            ("E1", "Droppoff_2"), # Via centrale as naar dropoff 2
            ("Entrance_1_3", "Droppoff_1"), # Pickup bij zij-ingang boven

            # --- Sector: Midden Magazijn (Rij D en C) ---
            ("D1", "Droppoff_3"), # Diagonaal door het magazijn
            ("D2", "Droppoff_2"),
            ("C1", "Droppoff_1"),
            ("C2", "Droppoff_3"),

            # --- Sector: Voorzijde (Rij B en A) ---
            ("B1", "Droppoff_2"),
            ("B2", "Droppoff_1"),
            ("Entrance_5_7", "Droppoff_3"), # Pickup bij zij-ingang onder
            ("A2", "Droppoff_2"),

            # --- Mix van uithoeken ---
            ("Entrance_2_4", "Droppoff_1"),
            ("F2", "Droppoff_2"),
            ("Entrance_6_8", "Droppoff_3"),
            ("E2", "Droppoff_1"),
            ("B1", "Droppoff_3"),
            ("D1", "Droppoff_2"),
            ("A1", "Droppoff_1"),
            ("F1", "Droppoff_3")
        ]

    def get_task_list(self, size):
        tasks_to_give = []

        for i in range(size):
            if(len(self.queue) > 0):            
                task = self.queue.pop(0)
                tasks_to_give.append(task)
            else:
                break
        
        return tasks_to_give
    
    def add_Task(self, task):
        self.queue.append(task)