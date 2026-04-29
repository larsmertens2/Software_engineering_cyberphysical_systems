"""
ROBOT CONTROLLER - Webots TurtleBot3 Warehouse Navigation

Bevat enkel de FSM-besturing. Hardware en berekeningen zitten in aparte modules:
- sensors.py:    kompas- en LIDAR-uitlezing
- motion.py:     motoraansturing
- navigation.py: kaart laden en routeberekening

States:
  IDLE         -> taak ophalen en route plannen
  WAITING      -> wachten op timer (geen route / gang bezet)
  ROTATING     -> draaien naar volgend waypoint
  MOVING       -> rijden naar waypoint met obstakeldetectie (slow_factor=3)
  MOVING_AISLE -> rijden in een gang: ganglocking + mildere reductie (slow_factor=1.5)

Referenties:
- Webots TurtleBot3 voorbeeld: https://github.com/cyberbotics/webots/blob/R2021b/projects/robots/robotis/turtlebot/controllers/turtlebot3_ostacle_avoidance/turtlebot3_ostacle_avoidance.c
- Webots-ontwikkelingsdocumentatie: https://pockerman-py-cubeai.readthedocs.io/en/latest/Examples/Webots/webots_ctrl_dev_101.html
"""

import math
import os
import sys
from controller import Robot

from sensors import get_direction, is_path_clear, detect_narrow_corridor, get_side_distances
from motion import drive
from navigation import load_map, get_route

parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(parent_dir)
from task_controller.task_controller import TaskManager


class RobotController:
    def __init__(self):
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())
        self.robot_name = self.robot.getName()

        self.taskmanager = TaskManager(self.robot_name)
        self.taskmanager.reset_all_locks()

        self.wait_until = 0.0

        # Configuratie
        self.max_speed = 4
        self.dist_error = 0.05
        self.angle_error = 0.04
        self.nearby_threshold = 0.5
        self.obstacle_threshold = 0.2
        self.normal_slow_factor = 3    # Snelheidsreductie bij object nabij (normaal rijden)
        self.aisle_slow_factor = 1.5   # Snelheidsreductie bij object nabij (in gang)

        # Motoren
        self.left_motor = self.robot.getDevice("left wheel motor")
        self.left_motor.setPosition(float('inf'))
        self.left_motor.setVelocity(0)
        self.right_motor = self.robot.getDevice("right wheel motor")
        self.right_motor.setPosition(float('inf'))
        self.right_motor.setVelocity(0)

        # Sensoren
        self.gps = self.robot.getDevice("GPS")
        self.gps.enable(self.time_step)
        self.compass = self.robot.getDevice("compass")
        self.compass.enable(self.time_step)
        self.lidar = self.robot.getDevice('LDS-01')
        self.lidar.enable(self.time_step)
        self.lidar.enablePointCloud()

        # Kaart & navigatie
        self.nodes, self.edges = load_map()

        dropoff_map = {
            "Bot_1": "Droppoff_1",
            "Bot_2": "Droppoff_2",
            "Bot_3": "Droppoff_3",
        }
        self.current_node = dropoff_map.get(self.robot_name, "Droppoff_2")
        self.target_node_index = 0
        self.route = []
        self.obstructed_nodes = []
        self.current_locked_aisle = None

        # Taakbeheer
        self.current_tasks_list = []
        self.current_task = None
        self.ReachedPackage = False

        # FSM
        self.state = "IDLE"
        self._state_handlers = {
            "IDLE":         self._state_idle,
            "WAITING":      self._state_waiting,
            "ROTATING":     self._state_rotating,
            "MOVING":       self._state_moving,
            "MOVING_AISLE": self._state_moving_aisle,
        }

    # -------------------------------------------------------------------------
    # Hoofdlus
    # -------------------------------------------------------------------------

    def _transition(self, new_state):
        if new_state != self.state:
            print(f"{self.robot_name}: {self.state} -> {new_state}")
            self.state = new_state

    def run(self):
        while self.robot.step(self.time_step) != -1:
            self._state_handlers[self.state]()

    # -------------------------------------------------------------------------
    # State handlers
    # -------------------------------------------------------------------------

    def _state_idle(self):
        """Haal een taak op en plan een route. Overgang naar ROTATING of WAITING."""
        if self.current_task is None:
            if self.current_tasks_list:
                self.current_task = self.current_tasks_list[0]
                print(f"{self.robot_name}: Nieuwe taak: Pickup {self.current_task[0]}")
            else:
                self.current_tasks_list = self.taskmanager.get_task_list(4)
                return  # Nog geen taak beschikbaar, volgende tick opnieuw proberen

        doel = self.current_task[1] if self.ReachedPackage else self.current_task[0]
        self.route = get_route(self.nodes, self.edges, self.current_node,
                               self.obstructed_nodes, doel)

        if not self.route:
            print(f"{self.robot_name}: Geen route naar {doel}! Wachten 30s...")
            self.wait_until = self.robot.getTime() + 30.0
            self._transition("WAITING")
        else:
            self.target_node_index = 0
            self._transition("ROTATING")

    def _state_waiting(self):
        """Wacht tot de timer verstreken is. Overgang naar IDLE."""
        if self.robot.getTime() >= self.wait_until:
            print(f"{self.robot_name}: Klaar met wachten, opnieuw plannen...")
            self._transition("IDLE")
        else:
            self._drive(0, 0)

    def _state_rotating(self):
        """Draai naar het volgende waypoint.

        Overgang naar MOVING_AISLE als target een gang is, anders naar MOVING.
        """
        position = self.gps.getValues()
        if math.isnan(position[0]):
            return

        angle_diff = self._calc_angle_diff(position, self.nodes[self.route[self.target_node_index]])

        if abs(angle_diff) > self.angle_error:
            val = -0.8 if angle_diff > 0 else 0.8
            self._drive(val, -val)
        else:
            target_name = self.route[self.target_node_index]
            self._transition("MOVING_AISLE" if "Ailse" in target_name else "MOVING")

    def _state_moving(self):
        """Rij naar een gewoon waypoint. Object nabij -> snelheid / 3.

        Overgangen:
          - Obstakel gedetecteerd        -> ROTATING (herplan terug naar huidig node)
          - Waypoint bereikt, nog route  -> ROTATING (volgend waypoint)
          - Waypoint bereikt, route klaar-> IDLE (taakstatus bijwerken)
        """
        self._navigate_to_waypoint(slow_factor=self.normal_slow_factor)

    def _state_moving_aisle(self):
        """Rij door een gang. Vergrendelt de gang en gebruikt mildere snelheidsreductie.

        Overgangen: zelfde als MOVING.
        """
        target_name = self.route[self.target_node_index]
        if not self._try_lock_aisle(target_name):
            return
        self._navigate_to_waypoint(slow_factor=self.aisle_slow_factor)

    def _navigate_to_waypoint(self, slow_factor):
        """Gedeelde rijlogica voor MOVING en MOVING_AISLE."""
        target_name = self.route[self.target_node_index]
        target_pos = self.nodes[target_name]

        position = self.gps.getValues()
        if math.isnan(position[0]):
            return

        distance = self._calc_distance(position, target_pos)
        angle_diff = self._calc_angle_diff(position, target_pos)

        # --- Obstakeldetectie ---
        if not is_path_clear(self.lidar, self.obstacle_threshold):
            self._handle_obstacle(target_name)
            return

        # --- Waypoint bereikt ---
        if distance <= self.dist_error:
            self._on_waypoint_reached(target_name)
            return

        # --- Rijden: GPS-correctie of wandcorrectie in smalle gang ---
        left_dist, right_dist = get_side_distances(self.lidar)
        if not detect_narrow_corridor(self.lidar):
            correction = angle_diff * 3.0
            self._drive(4.0 - correction, 4.0 + correction, slow_factor)
        else:
            correction = 0.0 if math.isinf(left_dist) or math.isinf(right_dist) \
                         else (left_dist - right_dist) * 3.0
            self._drive(self.max_speed + correction, self.max_speed - correction, slow_factor)

    # -------------------------------------------------------------------------
    # Hulpmethoden (geen state-logica)
    # -------------------------------------------------------------------------

    def _request_lock_aisle(self, aisle_id, current_node):
        msg = json.dumps({
            "type": "REQUEST_ENTRY",
            "robot_id": self.robot_name,
            "aisle": aisle_id,
            "node": current_node
        })
        self.emitter.send(msg.encode())
        seld.aisle_response = None

    def _try_lock_aisle(self, aisle_name):
        """Probeer een gang te vergrendelen. Geeft False terug als we (nog) moeten wachten."""
        current_time = self.robot.getTime()
        if current_time < self.wait_until:
            self._drive(0, 0)
            return False
        if not self.taskmanager.lock_aisle(aisle_name):
            print(f"{self.robot_name}: Gang {aisle_name} is bezet, wachten 10s...")
            self.wait_until = current_time + 10.0
            self._drive(0, 0)
            return False
        self.current_locked_aisle = True
        self.wait_until = 0.0
        print(f"{self.robot_name}: Gang {aisle_name} gelockt!")
        return True

    def _handle_obstacle(self, target_name):
        """Reageer op een geblokkeerd pad: voeg node toe aan obstructed en herplan."""
        self._drive(0, 0)
        self.obstructed_nodes.append(target_name)
        print(f"{self.robot_name}: Obstakel bij {target_name}! Terug naar {self.current_node}")

        if self.current_locked_aisle is not None and "Ailse" not in target_name:
            self.taskmanager.unlock_aisle()
            self.current_locked_aisle = None

        self.route = get_route(self.nodes, self.edges, self.current_node,
                               self.obstructed_nodes, self.current_node)
        self.target_node_index = 0
        self._transition("ROTATING")

    def _on_waypoint_reached(self, target_name):
        """Verwerk het bereiken van een waypoint en bepaal de volgende state."""
        print(f"{self.robot_name}: Node {target_name} bereikt")

        if "Ailse" not in target_name and self.current_node and "Ailse" in self.current_node:
            print(f"{self.robot_name}: Gang volledig verlaten, unlock sturen!")
            self.taskmanager.unlock_aisle()
            self.current_locked_aisle = None

        self.current_node = target_name
        self.target_node_index += 1

        if self.target_node_index < len(self.route):
            self._transition("ROTATING")
        else:
            self._on_route_finished()

    def _on_route_finished(self):
        """Verwerk het einde van een route: pickup/dropoff check, dan terug naar IDLE."""
        self._drive(0, 0)

        if self.current_task is not None:
            if self.current_node == self.current_task[0] and not self.ReachedPackage:
                print(f"{self.robot_name}: PAKKET OPGEHAALD")
                self.ReachedPackage = True

            elif self.current_node == self.current_task[1] and self.ReachedPackage:
                print(f"{self.robot_name}: TAAK VOLTOOID")
                self.taskmanager.complete_task(self.current_task[2])
                self.obstructed_nodes = []
                self.ReachedPackage = False
                self.current_tasks_list.pop(0)
                self.current_task = None

        self._transition("IDLE")

    def _calc_angle_diff(self, position, target_pos):
        dx = target_pos['x'] - position[0]
        dy = target_pos['y'] - position[1]
        target_angle = math.atan2(dy, dx)
        current_angle = get_direction(self.compass)
        return (target_angle - current_angle + math.pi) % (2 * math.pi) - math.pi

    def _calc_distance(self, position, target_pos):
        dx = target_pos['x'] - position[0]
        dy = target_pos['y'] - position[1]
        return math.sqrt(dx**2 + dy**2)

    def _drive(self, left_speed, right_speed, slow_factor=3):
        drive(self.left_motor, self.right_motor, left_speed, right_speed,
              self.lidar, self.nearby_threshold, slow_factor)


if __name__ == "__main__":
    robot = RobotController()
    robot.run()
