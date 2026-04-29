"""
ROBOT CONTROLLER - Webots TurtleBot3 Warehouse Navigation

Bevat enkel de FSM-besturing. Hardware en berekeningen zitten in aparte modules:
- sensors.py:    kompas- en LIDAR-uitlezing
- motion.py:     motoraansturing
- navigation.py: kaart laden en routeberekening

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

        # Motoren
        self.left_motor = self.robot.getDevice("left wheel motor")
        self.left_motor.setPosition(float('inf'))
        self.right_motor = self.robot.getDevice("right wheel motor")
        self.right_motor.setPosition(float('inf'))

        # Sensoren
        self.gps = self.robot.getDevice("GPS")
        self.gps.enable(self.time_step)
        self.compass = self.robot.getDevice("compass")
        self.compass.enable(self.time_step)
        self.lidar = self.robot.getDevice('LDS-01')
        self.lidar.enable(self.time_step)
        self.lidar.enablePointCloud()

        # FSM
        self.state = "IDLE"

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
        self.current_tasks_list = self.taskmanager.get_task_list(4)
        self.current_task = None
        self.ReachedPackage = False

    def _drive(self, left_speed, right_speed):
        drive(self.left_motor, self.right_motor, left_speed, right_speed,
              self.lidar, self.nearby_threshold)

    def _get_route(self, end_node):
        self.route = get_route(self.nodes, self.edges, self.current_node,
                               self.obstructed_nodes, end_node)

    def run(self):
        while self.robot.step(self.time_step) != -1:

            # === WAITING ===
            if self.state == "WAITING":
                if self.robot.getTime() >= self.wait_until:
                    print(f"{self.robot_name}: Klaar met wachten! Ik probeer opnieuw een route te plannen.")
                    self.state = "IDLE"
                else:
                    self._drive(0, 0)
                    continue

            # === ROUTE-EINDPUNT CHECK ===
            if not self.route or self.target_node_index >= len(self.route):
                self._drive(0, 0)

                if self.current_task is not None:
                    if self.current_node == self.current_task[0] and not self.ReachedPackage:
                        print("REACHED PACKAGE")
                        self.ReachedPackage = True

                    elif self.current_node == self.current_task[1] and self.ReachedPackage:
                        print("FINISHED TASK")
                        self.taskmanager.complete_task(self.current_task[2])
                        self.obstructed_nodes = []
                        self.ReachedPackage = False
                        self.current_tasks_list.pop(0)
                        self.current_task = None

                self.state = "IDLE"

            # === IDLE ===
            if self.state == "IDLE":
                if self.current_task is None:
                    if len(self.current_tasks_list) > 0:
                        self.current_task = self.current_tasks_list[0]
                        print(f"Nieuwe taak: Pickup {self.current_task[0]}")
                    else:
                        self.current_tasks_list = self.taskmanager.get_task_list(4)

                if self.current_task is not None:
                    doel = self.current_task[1] if self.ReachedPackage else self.current_task[0]
                    self._get_route(doel)

                    if not self.route:
                        print(f"{self.robot_name}: Geen route naar {doel}! Ik wacht 30s...")
                        self.state = "WAITING"
                        self.wait_until = self.robot.getTime() + 30.0
                    else:
                        self.target_node_index = 0
                        self.state = "ROTATING"
                else:
                    continue

            # === ROTATING & MOVING ===
            else:
                target_name = self.route[self.target_node_index]
                target_position = self.nodes[target_name]

                position = self.gps.getValues()
                if math.isnan(position[0]):
                    continue

                distance_x = target_position['x'] - position[0]
                distance_y = target_position['y'] - position[1]
                distance = math.sqrt(distance_x**2 + distance_y**2)
                target_angle = math.atan2(distance_y, distance_x)
                current_angle = get_direction(self.compass)
                angle_diff = (target_angle - current_angle + math.pi) % (2 * math.pi) - math.pi

                # === ROTATING ===
                if self.state == "ROTATING":
                    if abs(angle_diff) > self.angle_error:
                        val = -0.8 if angle_diff > 0 else 0.8
                        self._drive(val, -val)
                    else:
                        self.state = "MOVING"

                # === MOVING ===
                elif self.state == "MOVING":
                    left_dist, right_dist = get_side_distances(self.lidar)

                    # Gangsynchronisatie
                    if "Ailse" in target_name and self.current_locked_aisle is None:
                        current_time = self.robot.getTime()
                        if current_time >= self.wait_until:
                            if not self.taskmanager.lock_aisle(target_name):
                                print(f"{self.robot_name}: Gang {target_name} is bezet. Ik wacht 10 seconden...")
                                self.wait_until = current_time + 10.0
                                self._drive(0, 0)
                                continue
                            else:
                                self.current_locked_aisle = True
                                print(f"{self.robot_name} heeft de gang succesvol gelockt!")
                                self.wait_until = 0.0
                        else:
                            self._drive(0, 0)
                            continue

                    if not is_path_clear(self.lidar, self.obstacle_threshold):
                        self._drive(0, 0)
                        self.obstructed_nodes.append(target_name)
                        print(f"{self.robot_name}: Obstakel bij {target_name}! Ik keer terug naar {self.current_node}")

                        if self.current_locked_aisle is not None and "Ailse" not in target_name:
                            self.taskmanager.unlock_aisle()
                            self.current_locked_aisle = None

                        self._get_route(self.current_node)
                        self.target_node_index = 0
                        self.state = "ROTATING"

                    elif distance > self.dist_error and not detect_narrow_corridor(self.lidar):
                        correction = angle_diff * 3.0
                        self._drive(4.0 - correction, 4.0 + correction)

                    elif distance > self.dist_error:
                        if math.isinf(left_dist) or math.isinf(right_dist):
                            correction = 0.0
                        else:
                            correction = (left_dist - right_dist) * 3.0
                        self._drive(self.max_speed + correction, self.max_speed - correction)

                    else:
                        print(f"Node {target_name} reached")

                        if "Ailse" not in target_name and self.current_node and "Ailse" in self.current_node:
                            print(f"{self.robot_name}: Ik sta nu stevig op {target_name} en ben de gang volledig uit, API unlock sturen!")
                            self.taskmanager.unlock_aisle()
                            self.current_locked_aisle = None

                        self.current_node = target_name
                        self.target_node_index += 1
                        self.state = "ROTATING"


if __name__ == "__main__":
    robot = RobotController()
    robot.run()
