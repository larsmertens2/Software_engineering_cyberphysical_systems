"""
ROBOT CONTROLLER - Webots TurtleBot3 Warehouse Navigation

Dit bestand implementeert de hoofdbesturing voor autonome robots in een magazijn.
De robots navigeren naar pickup- en dropofflocaties, voorkomen obstakels,
en coördineren het gebruik van smalle gangen via een centrale taakmanager.

Gebruikte sensoren: GPS (locatie), Compass (richting), LIDAR (obstakeldetectie)
Gebruikte motoren: Linkerwiel en rechterwiel voor differentiële aandrijving

Referenties:
- Webots TurtleBot3 voorbeeld: https://github.com/cyberbotics/webots/blob/R2021b/projects/robots/robotis/turtlebot/controllers/turtlebot3_ostacle_avoidance/turtlebot3_ostacle_avoidance.c
- Webots-ontwikkelingsdocumentatie: https://pockerman-py-cubeai.readthedocs.io/en/latest/Examples/Webots/webots_ctrl_dev_101.html
"""

import json
import math
import os
import sys
from controller import Robot
from shortest_path import shortest_path

# Voeg parent directory toe aan path zodat we TaskManager kunnen importeren
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(parent_dir)
from task_controller.task_controller import TaskManager



class RobotController:
    """
    Hoofdcontroller voor de robot. Beheert navigatie, taakuitvoering,
    obstakeldetectie en coördinatie van gangen.
    """
    def __init__(self, warehouse_manager=None):
        """Initialiseer de robot, sensoren, motoren en taakmanager."""
        self.warehouse_manager = warehouse_manager
        
        # Webots robot instance
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())
        self.robot_name = self.robot.getName()  # Bijvoorbeeld: "Bot_1", "Bot_2"
        
        # Taakmanager voor database communicatie
        self.taskmanager = TaskManager(self.robot_name)
        self.taskmanager.reset_all_locks()  # Zorg dat deze robot geen locks meer heeft bij startup

        # Timing voor wachten (bijv. wanneer route niet beschikbaar is)
        self.wait_until = 0.0

        # === CONFIGURATIE PARAMETERS ===
        # Deze waarden bepalen het rijgedrag - kan geoptimaliseerd worden
        self.max_speed = 4                      # Maximale motorsnelheid (max is 6.28)
        self.dist_error = 0.05                  # Tolerantie afstand in meters
        self.angle_error = 0.04                 # Tolerantie draaihoek in radialen
        self.nearby_threshold = 0.5             # Afstand waarop obstakel detectie activeert
        self.obstacle_threshold = 0.2           # Afstand voor direct voor de robot (als te dicht = stoppen)
        self.view_angle = 30                    # Breedte scanhoek in graden (voor LIDAR)

        # === MOTOREN INITIALISATIE ===
        # Differentiële aandrijving: linkerwiel en rechterwiel kunnen onafhankelijk draaien
        self.left_motor = self.robot.getDevice("left wheel motor")
        self.left_motor.setPosition(float('inf'))  # Snelheid mode (niet positie mode)

        self.right_motor = self.robot.getDevice("right wheel motor")
        self.right_motor.setPosition(float('inf'))  # Snelheid mode

        # === SENSOREN INITIALISATIE ===
        # GPS: Absolute positie in het magazijn
        self.gps = self.robot.getDevice("GPS")
        self.gps.enable(self.time_step)

        # Kompas: Bepaal richting (x, y, z components die we omzetten naar hoek)
        self.compass = self.robot.getDevice("compass")
        self.compass.enable(self.time_step)
        
        # LIDAR: 360° afstandsensor voor obstakeldetectie
        # - Index 0-360 = hoeken in graden
        # - Index 180 = recht vooruit
        # - Index 90 = links
        # - Index 270 = rechts
        self.lidar = self.robot.getDevice('LDS-01')
        self.lidar.enable(self.time_step)
        self.lidar.enablePointCloud() 

        # === STATE MACHINE ===
        # De robot gaat door verschillende states:
        # - IDLE: Geen taak of route actief, planning nodig
        # - ROTATING: Draai naar volgende waypoint
        # - MOVING: Rij naar volgende waypoint
        # - WAITING: Wacht (route geblokkeerd of gang vergrendeld)
        self.state = "IDLE"
        
        # === KAART & NAVIGATIE ===
        # Laad knooppunten en verbindingen uit map.json
        self.load_map()
        
        # Elke robot start bij zijn eigen dropoff-zone
        dropoff_map = {
            "Bot_1": "Droppoff_1",
            "Bot_2": "Droppoff_2",
            "Bot_3": "Droppoff_3",
        }
        self.current_node = dropoff_map.get(self.robot_name, "Droppoff_2")  # Huidige locatie
        self.target_node_index = 0  # Index in self.route naar welke knoop gaan we nu
        self.route = []  # Geplande route (lijst van knoopnamen)
        self.obstructed_nodes = []  # Knoppen die geblokkeerd zijn (vermijden bij routeplanning)
        self.current_locked_aisle = None  # Heeft deze robot een gang vergrendeld?

        # === TAAKBEHEER ===
        self.current_tasks_list = self.taskmanager.get_task_list(4)  # Haal max 4 taken op
        self.current_task = None  # Huidige taak: (pickup_node, dropoff_node, task_id)
        self.ReachedPackage = False  # Zijn we al bij het pakket? (voor state tracking)
        

    def load_map(self):
        """Laad de magazijnkaart uit map.json (knooppunten en verbindingen)."""
        data_path = os.path.join(os.path.dirname(__file__), "map.json")
        with open(data_path, "r") as f:
            data = json.load(f)
            # nodes: dict {"node_name": {"x": float, "y": float}, ...}
            self.nodes = data["nodes"]
            # edges: lijst van verbindingen (momenteel niet gebruikt)
            self.edges = data["edges"]

    def get_direction(self):
        """Bepaal de huidige richting van de robot via kompas (in radialen).
        
        Returns:
            float: Hoek in radialen (-π tot π)
        """
        direction = self.compass.getValues()  # [x, y, z] componenten
        radians = math.atan2(direction[0], direction[1])  # Zet naar hoek
        return radians

    def get_route(self, obstructed_nodes, end_node):
        """Bereken de kortste route naar het doel, vermijdend geblokkeerde knoppen.
        
        Args:
            obstructed_nodes (list): Knoppen om te vermijden
            end_node (str): Doel knoopnaam
        """
        self.route = shortest_path(self.nodes, obstructed_nodes, self.edges, 
                                   self.current_node, end_node)
        print(f"Path: {self.route}")
    
    def object_nearby(self):
        """Controleer of er iets DICHT NABIJ is (breed scangebied).
        
        Dit wordt gebruikt in drive() om snelheid te verminderen als andere robots
        of obstakels in de buurt zijn.
        
        Returns:
            bool: True als iets dicht nabij is
        """
        range_image = self.lidar.getRangeImage()
        if not range_image: 
            return False

        # Scan 120° breed (60° links + recht + 60° rechts)
        vooruit_index = 180  # Index 180 = recht vooruit
        brede_view_angle = 120

        start_index = vooruit_index - (brede_view_angle // 2)
        eind_index = vooruit_index + (brede_view_angle // 2)
        
        for i in range(start_index, eind_index):
            index = i % 360
            distance = range_image[index]
            
            # Negeer ongeldige metingen
            if math.isinf(distance) or math.isnan(distance):
                continue
            
            if distance < self.nearby_threshold:
                return True 
                
        return False
    
    def drive(self, left_speed, right_speed):
        """Stuur beide wielen. Als iets dicht nabij is, verlaag snelheid tot 1/3.
        
        Args:
            left_speed (float): Snelheid linkerwiel
            right_speed (float): Snelheid rechterwiel
        """
        if self.object_nearby():
            # Voorzichtig rijden als ander object nabij is
            self.left_motor.setVelocity(left_speed / 3)
            self.right_motor.setVelocity(right_speed / 3)
        else: 
            # Normaal rijden
            self.left_motor.setVelocity(left_speed)
            self.right_motor.setVelocity(right_speed)

    def is_path_clear(self):
        """Controleer of de weg recht vooruit vrij is (smal scangebied).
        
        Dit wordt gebruikt om botsingen te voorkomen. Negeert muren aan de zijkant.
        
        Returns:
            bool: True als weg vrij, False als obstakel direct vooruit
        """
        range_image = self.lidar.getRangeImage()
        if not range_image: 
            return True

        # Scan slechts 30° (15° links, recht, 15° rechts) - vermijdt muurdetectie
        vooruit_index = 180  # Recht vooruit
        smalle_view_angle = 30

        start_index = vooruit_index - (smalle_view_angle // 2)
        eind_index = vooruit_index + (smalle_view_angle // 2)
        
        for i in range(start_index, eind_index):
            index = i % 360
            distance = range_image[index]
            
            if math.isinf(distance) or math.isnan(distance):
                continue
            
            # Obstakel direct vooruit = weg niet vrij
            if distance < self.obstacle_threshold:
                return False
                
        return True

    def detect_narrow_corridor(self):
        """Detecteer of de robot in een smalle gang zit (muren aan beide zijden dicht).
        
        In smalle gangen gebruiken we wandcorrectie ipv GPS-correctie voor betere stabiliteit.
        
        Returns:
            bool: True als beide zijmuren dicht bij zijn
        """
        range_image = self.lidar.getRangeImage()
        if not range_image: 
            return False

        # Controleer afstand links (index 90) en rechts (index 270)
        left_distance = range_image[90]
        right_distance = range_image[270]

        narrow_threshold = 0.4  # Meters - drempel voor smalle gang

        if left_distance < narrow_threshold and right_distance < narrow_threshold:
            # Beide zijden dicht = smalle gang
            return True
        
        return False
    
    def run(self):
        """Hoofdlus van de robot - runt totdat Webots stopt.
        
        State machine met stadia:
        1. WAITING: Wacht tot route beschikbaar is (of gang ontgrendeld)
        2. IDLE: Kies volgende taak en plan route
        3. ROTATING: Draai richting volgende waypoint
        4. MOVING: Rij naar waypoint met obstakeldetectie en gangsynchronisatie
        """
        while self.robot.step(self.time_step) != -1:

            # === FASE 1: WACHTTIJD HANDLING ===
            # Robot wacht als route geblokkeerd is of gang vergrendeld door ander
            if self.state == "WAITING":
                if self.robot.getTime() >= self.wait_until:
                    # Wachttijd voorbij - probeer opnieuw
                    print(f"{self.robot_name}: Klaar met wachten! Ik probeer opnieuw een route te plannen.")
                    self.state = "IDLE"
                else:
                    # Nog wachten
                    self.drive(0, 0)
                    continue

            # === FASE 2: ROUTE-EINDPUNT CHECK ===
            # Heeft de robot een waypoint bereikt of geen route meer?
            if not self.route or self.target_node_index >= len(self.route):
                self.drive(0, 0)  # Stop rijden
                
                # Controleer of we een taak kunnen voltooien
                if self.current_task is not None:
                    # Stap 1: Zijn we bij het PICKUP-punt gekomen?
                    if self.current_node == self.current_task[0] and not self.ReachedPackage:
                        print("REACHED PACKAGE")
                        self.ReachedPackage = True
                        
                    # Stap 2: Zijn we bij het DROPOFF-punt gekomen?
                    elif self.current_node == self.current_task[1] and self.ReachedPackage:
                        print("FINISHED TASK")
                        
                        # Taak afmelden in database
                        current_task_id = self.current_task[2]
                        self.taskmanager.complete_task(current_task_id)
                        
                        # Reset state voor volgende taak
                        self.obstructed_nodes = []
                        self.ReachedPackage = False
                        self.current_tasks_list.pop(0)
                        self.current_task = None
                
                # Ga terug naar IDLE voor taakplanning
                self.state = "IDLE"

            # === FASE 3: TAAKPLANNING (IDLE STATE) ===
            # In IDLE state: haal nieuwe taak op en plan route
            if self.state == "IDLE":
                # Stap 1: Haal nieuwe taak op als we er geen hebben
                if self.current_task is None:
                    if len(self.current_tasks_list) > 0:
                        # Neem volgende taak uit lokale lijst
                        self.current_task = self.current_tasks_list[0]
                        print(f"Nieuwe taak: Pickup {self.current_task[0]}")
                    else:
                        # Lokale lijst leeg - vraag meer taken aan API
                        self.current_tasks_list = self.taskmanager.get_task_list(4)
                
                # Stap 2: Plan route naar pickup of dropoff
                if self.current_task is not None:
                    # Bepaal doel: pickup als niet bereikt, anders dropoff
                    doel = self.current_task[1] if self.ReachedPackage else self.current_task[0]
                    self.get_route(self.obstructed_nodes, doel)

                    if not self.route:
                        # Route niet mogelijk - wacht 30s en probeer opnieuw
                        print(f"{self.robot_name}: Geen route naar {doel}! Ik wacht 30s...")
                        self.state = "WAITING"
                        self.wait_until = self.robot.getTime() + 30.0
                    else:
                        # Route gevonden - start navigatie
                        self.target_node_index = 0
                        self.state = "ROTATING"
                else:
                    # Geen taak - wacht volgende iteratie
                    continue

            # === FASE 4: NAVIGATIE (ROTATING & MOVING STATES) ===
            # Voer navigatie uit (niet in IDLE state)
            else:
                # Haal huidige target waypoint op
                target_name = self.route[self.target_node_index]
                target_position = self.nodes[target_name]

                # Haal huidige positie op via GPS
                position = self.gps.getValues()
                if math.isnan(position[0]):
                    continue  # Skip als GPS ongeldig

                # === BEREKENINGEN: afstand en hoek naar target ===
                distance_x = target_position['x'] - position[0]
                distance_y = target_position['y'] - position[1]
                distance = math.sqrt(distance_x**2 + distance_y**2)
                target_angle = math.atan2(distance_y, distance_x)  # Gewenste hoek
                current_angle = self.get_direction()  # Huidige hoek
                # Normaliseer hoekverschilje tot [-π, π]
                angle_diff = (target_angle - current_angle + math.pi) % (2 * math.pi) - math.pi

                # Check of weg vrij is (voor obstakeldetectie)
                path_is_clear = self.is_path_clear()

                # === SUBSTATE: ROTATING ===
                # Draai totdat we in de juiste richting kijken
                if self.state == "ROTATING":
                    if abs(angle_diff) > self.angle_error:
                        # Draai in richting van angle_diff
                        # Positief angle_diff = linksom draaien
                        val = -0.8 if angle_diff > 0 else 0.8
                        self.drive(val, -val)
                    else:
                        # Hoek bereikt - start rijden
                        self.state = "MOVING"
                
                elif self.state == "MOVING":
                    # Zijafstanden voor wandcorrectie in smalle gangen
                    range_image = self.lidar.getRangeImage()
                    self.left_distance = range_image[90]   # Links
                    self.right_distance = range_image[270] # Rechts

                    # === GANGSYNCHRONISATIE ===
                    # Vergrendel gang (Aisle) zodat ander robot niet tegelijk inrijdt
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

                        # Keer terug naar vorige node en herplan route ALTIJD met obstructed_nodes
                        self.get_route(self.obstructed_nodes, self.current_node)
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


# === PROGRAMMA START ===
if __name__ == "__main__":
    robot = RobotController()
    robot.run()