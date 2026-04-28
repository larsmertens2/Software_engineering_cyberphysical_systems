import json
import math
import os
import sys
from controller import Robot
from shortest_path import shortest_path

# Some parts of this controller are deviated from an example controller (written in c. So a different language, but the logic/implemted-steps have a big overlap):
#   https://github.com/cyberbotics/webots/blob/R2021b/projects/robots/robotis/turtlebot/controllers/turtlebot3_ostacle_avoidance/turtlebot3_ostacle_avoidance.c

# This documentation helped building the controller:
#   https://pockerman-py-cubeai.readthedocs.io/en/latest/Examples/Webots/webots_ctrl_dev_101.html


# importing other controllers
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(parent_dir)

# Nu kun je importeren vanuit de andere submap
from task_controller.task_controller import TaskManager



class RobotController:
    def __init__(self):
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())
        self.robot_name = self.robot.getName() 
        self.taskmanager = TaskManager(self.robot_name)

        # Settings:
        #TODO: optimize these settings
        self.max_speed = 4 # Max is 6.28
        self.dist_error = 0.05 # Meters
        self.angle_error = 0.04 # Radians
        self.obstacle_threshold = 0.2  # Afstand in meters
        self.view_angle = 90 # Graden om te scannen /2 links, /2 rechts

        # Motors
        self.left_motor = self.robot.getDevice("left wheel motor")
        self.left_motor.setPosition(float('inf'))

        self.right_motor = self.robot.getDevice("right wheel motor")
        self.right_motor.setPosition(float('inf'))

        # Sensors
        self.gps = self.robot.getDevice("GPS")
        self.gps.enable(self.time_step)

        self.compass = self.robot.getDevice("compass")
        self.compass.enable(self.time_step)
        
        self.lidar = self.robot.getDevice('LDS-01')
        self.lidar.enable(self.time_step)
        self.lidar.enablePointCloud() 

        # States:
        # Possible states: ROTATING, MOVING, IDLE, ... #TODO with more advanced steps later in the project (collision preventiopn etc...)
        self.state = "IDLE"

        # Map:
        self.load_map()
        dropoff_map = {
        "Bot_1": "Droppoff_1",
        "Bot_2": "Droppoff_2",
        "Bot_3": "Droppoff_3",
        }  
        self.current_node = dropoff_map.get(self.robot_name, "Droppoff_2")
        self.target_node_index = 0
        self.route = []
        self.obstructed_nodes = [] # List van nodes die momenteel geblokkeerd zijn (om later te gebruiken in de routeplanning)

        #initialising Taskmanager
        self.taskmanager = TaskManager(self.robot_name)
        self.current_tasks_list = self.taskmanager.get_task_list(4)      # De lijst met taken die we van de manager krijgen
        self.final_destination = None   # De dropoff van de huidige taak
        self.current_task = None
        self.ReachedPackage = False

    def load_map(self):
        data_path = os.path.join(os.path.dirname(__file__), "map.json")
        with open(data_path, "r") as f:
            data = json.load(f)
            self.nodes = data["nodes"]
            self.edges = data["edges"] # unused in current code? to be deleted?

    def get_direction(self):
        direction = self.compass.getValues()
        radians = math.atan2(direction[0], direction[1])
        return radians

    def get_route(self, obstructed_nodes, end_node):
        self.route = shortest_path(self.nodes, obstructed_nodes, self.edges, self.current_node, end_node)
        print(f"Path: {self.route}")

    def drive(self, left_speed, right_speed):
        self.left_motor.setVelocity(left_speed)
        self.right_motor.setVelocity(right_speed)

    def is_path_clear(self):
        range_image = self.lidar.getRangeImage()
        if not range_image: 
            return True

        # Instellingen voor de scan
        vooruit_index = 180  # Lidar sensor staat achterstevoren
        kijkhoek = self.view_angle        # Hoeveel graden we in scannen (20 links, 20 rechts)
        
        # We berekenen de indices die we willen controleren 160-200 graden
        start_index = vooruit_index - (kijkhoek // 2)
        eind_index = vooruit_index + (kijkhoek // 2)
        
        for i in range(start_index, eind_index):
            # Gebruik gehele getallen om binnen de lijst-index te blijven
            index = i % 360
            distance = range_image[index]
            
            # Check of er iets binnen de drempelwaarde is
            if distance < self.obstacle_threshold:
                return False
                
        return True
    
    def run(self):
        while self.robot.step(self.time_step) != -1:
            # 1. CHECK: Zijn we op een eindbestemming?
            if not self.route or self.target_node_index >= len(self.route):
                self.drive(0, 0)
                
                # Check of we bij pickup of dropoff zijn (gebruik ==)
                if self.current_task is not None:
                    if self.current_node == self.current_task[0] and not self.ReachedPackage:
                        print("REACHED PACKAGE")
                        self.ReachedPackage = True
                    elif self.current_node == self.current_task[1] and self.ReachedPackage:
                        print("FINISHED TASK")
                        
                        # 1. Haal de ID op (zat op plek 3 in de lijst)
                        current_task_id = self.current_task[2]
                        
                        # 2. Meld de taak af bij de database
                        self.taskmanager.complete_task(current_task_id)
                        
                        # Reset de lijst van geblokkeerde nodes bij het voltooien van een taak
                        self.obstructed_nodes = []

                        # 3. Reset voor de volgende taak
                        self.ReachedPackage = False
                        self.current_tasks_list.pop(0)
                        self.current_task = None
                
                self.state = "IDLE"

            # 2. PLANNING OF RIJDEN
            if self.state == "IDLE":
                print("idle")
                if self.current_task is None:
                    if len(self.current_tasks_list) > 0:
                        self.current_task = self.current_tasks_list[0]
                        print(f"Nieuwe taak: Pickup {self.current_task[0]}")
                    else:
                        self.current_tasks_list = self.taskmanager.get_task_list(4)
                        print("ASKED API")
                
                if self.current_task is not None:
                    doel = self.current_task[1] if self.ReachedPackage else self.current_task[0]
                    self.get_route(self.obstructed_nodes, doel)
                    self.target_node_index = 0
                    self.state = "ROTATING"
                else:
                    continue

            # 3. NAVIGATIE (Alleen uitvoeren als we NIET idle zijn)
            else:
                target_name = self.route[self.target_node_index]
                target_position = self.nodes[target_name]

                position = self.gps.getValues()
                if math.isnan(position[0]): continue

                # Berekeningen (afstand/hoek)
                distance_x = target_position['x'] - position[0]
                distance_y = target_position['y'] - position[1]
                distance = math.sqrt(distance_x**2 + distance_y**2)
                target_angle = math.atan2(distance_y, distance_x)
                current_angle = self.get_direction()
                angle_diff = (target_angle - current_angle + math.pi) % (2 * math.pi) - math.pi

                path_is_clear = self.is_path_clear()

                if self.state == "ROTATING":
                    if abs(angle_diff) > self.angle_error:
                        val = -0.8 if angle_diff > 0 else 0.8
                        self.drive(val, -val)
                    else:
                        self.state = "MOVING"
                
                elif self.state == "MOVING":
                    if not path_is_clear:
                        # STOP de robot als het pad niet vrij is
                        self.drive(0, 0)
                        self.state = "IDLE"  # Terug naar idle
                        self.obstructed_nodes.append(target_name)  # Voeg deze node toe aan de lijst van geblokkeerde nodes
                        print(f"Node {target_name} is obstructed")
                        self.route = []  # Wis de huidige route zodat er een nieuwe route gepland wordt in de volgende iteratie

                    elif distance > self.dist_error:
                        correction = angle_diff * 3.0
                        self.drive(4.0 - correction, 4.0 + correction)
                    else:
                        print(f"Node {target_name} reached")
                        self.current_node = target_name 
                        self.target_node_index += 1     # Verhoog teller
                        self.state = "ROTATING"


robot = RobotController()
robot.run()