import sys
import os

current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.append(current_dir)

from task_controller.task_controller import TaskManager
from robot_controller.robot_controller import RobotController

class WarehouseManager:
    def __init__(self):
        self.task_manager = TaskManager("Manager") 
        
        self.robots = [] # lijst van alle bots
        self.pending_tasks = self.task_manager.get_task_list(10)
        
        # Houdt bij welke gang door welke robot bezet is. Formaat: {"Aisle_1": "Bot_1"}
        self.locked_aisles = {} 

    def is_aisle_clear(self, aisle_name):
        """Controleert of een gang vrij is."""
        return aisle_name not in self.locked_aisles

    def lock_aisle(self, robot_id, aisle_name):
        """Probeert een gang te locken voor een specifieke robot."""
        if self.is_aisle_clear(aisle_name):
            self.locked_aisles[aisle_name] = robot_id
            print(f"[MANAGER] {aisle_name} is nu GELOCKED door {robot_id}")
            return True
        return False

    def unlock_aisle(self, robot_id):
        """Unlocks alle gangen die door deze specifieke robot bezet zijn."""
        # We maken een kopie van de keys met list() om de dictionary veilig aan te passen tijdens de loop
        for aisle in list(self.locked_aisles.keys()):
            if self.locked_aisles[aisle] == robot_id:
                del self.locked_aisles[aisle]
                print(f"[MANAGER] {aisle} is VRIJGEGEVEN door {robot_id}")

    def assign_tasks(self):
        """Verdeel taken over robots die IDLE zijn."""
        pass

    def update(self):
        """Hoofdloop van de manager."""
        self.assign_tasks()