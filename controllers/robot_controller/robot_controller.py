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
    def __init__(self, warehouse_manager=None):
        self.warehouse_manager = warehouse_manager
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())
        self.robot_name = self.robot.getName()
        self.taskmanager = TaskManager(self.robot_name)
        self.taskmanager.reset_all_locks()

        self.wait_until = 0.0

        # Settings:
        #TODO: optimize these settings
        self.max_speed = 4 # Max is 6.28
        self.dist_error = 0.05 # Meters
        self.angle_error = 0.04 # Radians
        self.nearby_threshold = 0.5 # Meters, voor obstakel detectie
        self.obstacle_threshold = 0.2  # Afstand in meters
        self.view_angle = 30 # Graden om te scannen /2 links, /2 rechts

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
        # Possible states: ROTATING, MOVING, IDLE, WAITING, ... #TODO with more advanced steps later in the project (collision preventiopn etc...)
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
        self.current_locked_aisle = None

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
    
    def object_nearby(self):
        range_image = self.lidar.getRangeImage()
        if not range_image: 
            return False

        vooruit_index = 180 
        brede_view_angle = 120  # Breed! Ideaal om robots in de ooghoeken te spotten

        start_index = vooruit_index - (brede_view_angle // 2)
        eind_index = vooruit_index + (brede_view_angle // 2)
        
        for i in range(start_index, eind_index):
            index = i % 360
            distance = range_image[index]
            
            # Negeer metingen die "oneindig" of ongeldig zijn
            if math.isinf(distance) or math.isnan(distance):
                continue
            
            if distance < self.nearby_threshold:
                return True 
                
        return False
    
    def drive(self, left_speed, right_speed):
        if self.object_nearby():
            self.left_motor.setVelocity(left_speed/3)
            self.right_motor.setVelocity(right_speed/3)
        else: 
            self.left_motor.setVelocity(left_speed)
            self.right_motor.setVelocity(right_speed)

    def is_path_clear(self):
        range_image = self.lidar.getRangeImage()
        if not range_image: 
            return True

        vooruit_index = 180 
        smalle_view_angle = 30  # Smal! Zodat hij de muren in de gang negeert

        start_index = vooruit_index - (smalle_view_angle // 2)
        eind_index = vooruit_index + (smalle_view_angle // 2)
        
        for i in range(start_index, eind_index):
            index = i % 360
            distance = range_image[index]
            
            if math.isinf(distance) or math.isnan(distance):
                continue
            
            # Alleen stoppen als er écht iets recht voor onze neus staat
            if distance < self.obstacle_threshold:
                return False
                
        return True

    def detect_narrow_corridor(self):
        range_image = self.lidar.getRangeImage()
        if not range_image: 
            return False

        # We controleren de zijwaartse scans (90 graden links en rechts)
        left_distance = range_image[90]
        right_distance = range_image[270]

        narrow_threshold = 0.4  # Drempelwaarde voor het detecteren van een smalle doorgang

        if left_distance < narrow_threshold and right_distance < narrow_threshold:
            return True #als beide zijden dicht zijn, is er waarschijnlijk een smalle doorgang
        
        return False
    
    def run(self):
        while self.robot.step(self.time_step) != -1:

            #als we moeten wachten omdat er geen route beschikbaar is
            if self.state == "WAITING":
                # Check of er al 30 seconden (simulatietijd) verstreken zijn
                if self.robot.getTime() >= self.wait_until:
                    print(f"{self.robot_name}: Klaar met wachten! Ik probeer opnieuw een route te plannen.")
                    self.state = "IDLE"
                else:
                    self.drive(0, 0)
                    continue

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
                # print("idle")
                if self.current_task is None:
                    if len(self.current_tasks_list) > 0:
                        self.current_task = self.current_tasks_list[0]
                        print(f"Nieuwe taak: Pickup {self.current_task[0]}")
                    else:
                        self.current_tasks_list = self.taskmanager.get_task_list(4)
                        # print("ASKED API")
                
                if self.current_task is not None:
                    doel = self.current_task[1] if self.ReachedPackage else self.current_task[0]
                    self.get_route(self.obstructed_nodes, doel)

                    # als er geen route gevonden wordt
                    if not self.route:
                        print(f"{self.robot_name}: Geen route gevonden naar {doel}! Ik ga 30 seconden wachten...")
                        self.state = "WAITING"
                        self.wait_until = self.robot.getTime() + 30.0
                        
                        # We resetten de obstructed_nodes zodat hij over 30s met een schone lei opnieuw zoekt
                        self.obstructed_nodes = [] 
                    else:
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
                    range_image = self.lidar.getRangeImage()
                    self.left_distance = range_image[90]  # Rechts of links van de robot
                    self.right_distance = range_image[270]  # andere kant van de robot

                    # Check of het een Ailse is EN of we deze specifieke node niet al zélf gelockt hebben
                    if "Ailse" in target_name and self.current_locked_aisle is None: 
                        current_time = self.robot.getTime()
                        
                        # Mogen we al een nieuwe API request doen (tijd is voorbij wait_until)?
                        if current_time >= self.wait_until:
                            lock_succes = self.taskmanager.lock_aisle(target_name)
                            
                            if not lock_succes:
                                print(f"{self.robot_name}: Gang {target_name} is bezet. Ik wacht 10 seconden...")
                                # Hergebruik van je bestaande variabele!
                                self.wait_until = current_time + 10.0 
                                self.drive(0, 0)
                                continue
                            else:
                                self.current_locked_aisle = True  
                                print(f"{self.robot_name} heeft de gang succesvol gelockt!")
                                # Reset wait_until voor de netheid, al overschrijft de code hem toch indien nodig
                                self.wait_until = 0.0 
                        else:
                            # We zitten nog in de 10-seconden wachttijd.
                            self.drive(0, 0)
                            continue

                    if not path_is_clear:
                        self.drive(0, 0)
                        self.obstructed_nodes.append(target_name)
                        print(f"{self.robot_name}: Obstakel bij {target_name}! Ik keer terug naar {self.current_node}")
                        
                        if self.current_locked_aisle is not None and "Ailse" not in target_name:
                            self.taskmanager.unlock_aisle()
                            self.current_locked_aisle = None

                        # Vervang de hele route door alleen de vorige node
                        self.route = [self.current_node] 
                        self.target_node_index = 0
                        self.state = "ROTATING"
                    
                    elif distance > self.dist_error and not self.detect_narrow_corridor():
                        correction = angle_diff * 3.0
                        self.drive(4.0 - correction, 4.0 + correction)
                        # print("GPS correction")

                    elif distance > self.dist_error:
                        # Haal afstanden op
                        l_dist = self.left_distance
                        r_dist = self.right_distance
                        
                        # Voorkom wiskundige fouten (inf - inf = NaN)
                        if math.isinf(l_dist) or math.isinf(r_dist):
                            correction = 0.0
                        else:
                            error = l_dist - r_dist
                            correction = error * 3.0 
                            
                        self.drive(self.max_speed + correction, self.max_speed - correction)

                    else:
                        print(f"Node {target_name} reached")

                        # We zijn nu fysiek op de nieuwe node. Als dit géén gang is, maar we kwamen wel uit een gang:
                        if "Ailse" not in target_name and self.current_node and "Ailse" in self.current_node:
                            print(f"{self.robot_name}: Ik sta nu stevig op {target_name} en ben de gang volledig uit, API unlock sturen!")
                            self.taskmanager.unlock_aisle()
                            self.current_locked_aisle = None

                        self.current_node = target_name 
                        self.target_node_index += 1     
                        self.state = "ROTATING"


robot = RobotController()
robot.run()