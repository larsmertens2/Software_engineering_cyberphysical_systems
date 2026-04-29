"""
ROBOT CONTROLLER - Webots TurtleBot3 Warehouse Navigation

This controller only implements the final state machine of the robot, the following documents contain the listed functions:
- sensors.py:    compass and lidar readings
- motion.py:     motor control
- navigation.py: loading map and calculating route

States:
  IDLE:             Retrieve task, plan a route
  WAITING:          wait for timer to expire
  ROTATING:         rotate to next waypoint
  MOVING:           move towards next waypoint, use obstacle detection
  MOVING_AISLE:     drive in an aisle, lock the aisle.
  WAITING_AISLE:    wait for permission to enter aisle

Referenties:
- Webots TurtleBot3 voorbeeld: https://github.com/cyberbotics/webots/blob/R2021b/projects/robots/robotis/turtlebot/controllers/turtlebot3_ostacle_avoidance/turtlebot3_ostacle_avoidance.c
- Webots-ontwikkelingsdocumentatie: https://pockerman-py-cubeai.readthedocs.io/en/latest/Examples/Webots/webots_ctrl_dev_101.html
"""

import json
import math
import os
import sys
import urllib.request
import urllib.error
import time

from sensors import get_direction, is_path_clear, detect_narrow_corridor, get_side_distances
from motion import drive
from navigation import load_map, get_route
from controllers.robot_hal import create_robot_hal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(parent_dir)
from controllers.task_manager.task_manager import TaskManager


class RobotController:
    def __init__(self):
        self.hal = create_robot_hal()
        self.time_step = self.hal.get_time_step()
        self.robot_name = self.hal.get_name()

        self.taskmanager = TaskManager(self.robot_name)

        self.wait_until = 0.0

        # Configuration
        self.max_speed = 4
        self.dist_error = 0.05
        self.angle_error = 0.04
        self.nearby_threshold = 0.5
        self.obstacle_threshold = 0.2
        self.normal_slow_factor = 3    # Speed reduction when close to an object
        self.aisle_slow_factor = 1.5   # speed reduction when in a narrow aisle

        # Motors
        self.left_motor = self.hal.left_motor
        self.left_motor.setPosition(float('inf'))
        self.left_motor.setVelocity(0)
        self.right_motor = self.hal.right_motor
        self.right_motor.setPosition(float('inf'))
        self.right_motor.setVelocity(0)

        # Sensors
        self.gps = self.hal.gps
        self.gps.enable(self.time_step)
        self.compass = self.hal.compass
        self.compass.enable(self.time_step)
        self.lidar = self.hal.lidar
        self.lidar.enable(self.time_step)
        self.lidar.enablePointCloud()

        # Communication with aisle devices
        self.emitter = self.hal.getDevice("Emitter")
        self.receiver = self.hal.getDevice("Receiver")
        self.receiver.enable(self.time_step)
        self.aisle_response = None

        # Map & navigation
        self.nodes, self.edges = load_map()

        dropoff_map = {
            "Bot_1": "Droppoff_1",
            "Bot_2": "Droppoff_2",
            "Bot_3": "Droppoff_3",
        }
        self.current_node = dropoff_map.get(self.robot_name)
        self.target_node_index = 0
        self.route = []
        self.obstructed_nodes = []
        self.current_locked_aisle = None

        # Task management
        self.current_tasks_list = []
        self.current_task = None
        self.ReachedPackage = False

        # Final State Machine
        self.state = "IDLE"
        self._state_handlers = {
            "IDLE":          self._state_idle,
            "WAITING":       self._state_waiting,
            "ROTATING":      self._state_rotating,
            "MOVING":        self._state_moving,
            "MOVING_AISLE":  self._state_moving_aisle,
            "WAITING_AISLE": self._state_waiting_aisle,
        }

        # Emergency stop state
        self.emergency_active = False
        self.last_emergency_check = 0
        self.emergency_check_interval = 0.5  # Check each 0.5 seconds

    # -------------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------------

    def _transition(self, new_state):
        # Print the change of state and actually update the state
        if new_state != self.state:
            print(f"{self.robot_name}: {self.state} -> {new_state}")
            self.state = new_state

    def run(self):
        # Main loop: do actions based on the current state, check for possible state changes and poll for messages from aisle devices.
        while self.hal.step(self.time_step) != -1:
            # Check emergency status
            self._check_emergency_status()
            
            # If emergency is active, stop motors immediately
            if self.emergency_active:
                self._drive(0, 0)
                print(f"{self.robot_name}: EMERGENCY ACTIVE - MOTORS STOPPED")
                continue
            
            self._poll_receiver()
            self._state_handlers[self.state]()

    # -------------------------------------------------------------------------
    # State handlers
    # -------------------------------------------------------------------------

    def _state_idle(self):
        # Request a new task, plan the next route
        if self.current_task is None:
            if self.current_tasks_list:
                self.current_task = self.current_tasks_list[0]
                print(f"{self.robot_name}: New task: Pickup {self.current_task[0]}")
            else:
                if self.hal.get_time() < self.wait_until:
                    return  # Throttle: Wait before claiming again
                self.current_tasks_list = self.taskmanager.get_task_list(1)
                if not self.current_tasks_list:
                    self.wait_until = self.hal.get_time() + 2.0  # 2s wait for next attempt
                    self.route = []           
                    self.current_task = None  
                    self._drive(0, 0)        
                    return                    
                return  # No task available (yet)

        # Get new objective, plan route
        doel = self.current_task[1] if self.ReachedPackage else self.current_task[0]
        self.route = get_route(self.nodes, self.edges, self.current_node,
                               self.obstructed_nodes, doel)

        if not self.route:
            # No route found: enter wait state
            print(f"{self.robot_name}: No route to {doel}! Wait 30s...")
            self.wait_until = self.hal.get_time() + 30.0
            self._transition("WAITING")
        else:
            # Route found: start rotating for next node
            self.target_node_index = 0
            self._transition("ROTATING")

    def _state_waiting(self):
        """Wait till timer expires, then return idle for a new attempt at a route or task claim

        State changes: IDLE after timer expires
        """
        if self.hal.get_time() >= self.wait_until:
            print(f"{self.robot_name}: Done waiting, new attempt at a route or claiming a task...")
            self._transition("IDLE")
        else:
            self._drive(0, 0)

    def _state_rotating(self):
        """Rotate to next waypoint/node.

        State changes: MOVING or MOVING_AISLE after rotation is complete
        """
        position = self.gps.get_position()
        if math.isnan(position[0]):
            return

        # Calculate angle difference to next node
        angle_diff = self._calc_angle_diff(position, self.nodes[self.route[self.target_node_index]])

        if abs(angle_diff) > self.angle_error:
            # If angle is too large, rotate to make the difference smaller.
            val = -0.8 if angle_diff > 0 else 0.8
            self._drive(val, -val)
        else:
            # If angle is small enough, start moving. Either in a hallway or normal.
            target_name = self.route[self.target_node_index]
            if "Aisle" in target_name:
                # Moving towards/in aisle
                if "Aisle" not in self.current_node:
                    # Aisle-version: ask permission to enter.
                    self._request_aisle_entry(target_name, self.current_node)
                    self._transition("WAITING_AISLE")
                else:
                    # Al in de gang, geen nieuwe request nodig
                    self._transition("MOVING_AISLE")
            else:
                # Normal moving
                self._transition("MOVING")

    def _state_moving(self):
        """ Drive towards next waypoint/node. Slow down if close to obstacle.

        State changes:
          - Obstacle detected:                      ROTATING (reroute to current node)
          - Waypoint reached, route unfinished:     ROTATING (move - rotate first - to next node)
          - Waypoint reached, route finished:       IDLE (check tasks)
        """
        self._navigate_to_waypoint(slow_factor=self.normal_slow_factor)

    def _state_moving_aisle(self):
        """Move through aisle, lesser speed correction.

        State changes: similar to MOVING.
        """
        self._navigate_to_waypoint(slow_factor=self.aisle_slow_factor)

    def _state_waiting_aisle(self):
        """Wait for GRANTED message of aisle device. Don't drive.
        
        State changes: MOVING_AISLE if ENTRY_GRANTED received, ROTATING if timer expires
        """
        self._drive(0, 0)
        if self.aisle_response == "ENTRY_GRANTED":
            self.aisle_response = None
            self._transition("MOVING_AISLE")

    # -------------------------------------------------------------------------
    # Help functions
    # -------------------------------------------------------------------------

    def _navigate_to_waypoint(self, slow_factor):
        # Logic when moving towards the next node
        target_name = self.route[self.target_node_index]
        target_pos = self.nodes[target_name]

        position = self.gps.get_position()
        if math.isnan(position[0]):
            return

        distance = self._calc_distance(position, target_pos)
        angle_diff = self._calc_angle_diff(position, target_pos)

        # Obstacle detection
        if not is_path_clear(self.lidar, self.obstacle_threshold):
            self._handle_obstacle(target_name)
            return

        # Arrived at waypoint
        if distance <= self.dist_error:
            self._on_waypoint_reached(target_name)
            return

        # Drive: GPS correction, lidar correction in aisle
        left_dist, right_dist = get_side_distances(self.lidar)
        if not detect_narrow_corridor(self.lidar):
            correction = angle_diff * 3.0
            self._drive(4.0 - correction, 4.0 + correction, slow_factor)
        else:
            correction = 0.0 if math.isinf(left_dist) or math.isinf(right_dist) \
                         else (left_dist - right_dist) * 3.0
            self._drive(self.max_speed + correction, self.max_speed - correction, slow_factor)

    def _check_emergency_status(self):
        # Poll the backend for emergency status."""
        current_time = time.time()
        
        # Throttle: check each N seconds
        if current_time - self.last_emergency_check < self.emergency_check_interval:
            return
        
        self.last_emergency_check = current_time
        
        try:
            with urllib.request.urlopen(
                'http://localhost:5000/api/emergency',
                timeout=1
            ) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    self.emergency_active = data.get('emergency_active', False)
                    
                    # Log state changes
                    if self.emergency_active:
                        print(f"{self.robot_name}: EMERGENCY ACTIVATED!")
        except urllib.error.URLError as e:
            print(f"{self.robot_name}: Error checking emergency status: {e}")
        except Exception as e:
            print(f"{self.robot_name}: Unexpected error checking emergency: {e}")

    def _get_base_aisle(self, node_name):
        """Returns the base aisle: 'Aisle_1_2' -> 'Aisle_1'."""
        parts = node_name.split("_")
        return "_".join(parts[:2])

    def _request_aisle_entry(self, node_name, current_node):
        # Request entry to aisle
        base = self._get_base_aisle(node_name)
        self.current_locked_aisle = base
        self.aisle_response = None
        msg = json.dumps({
            "type": "REQUEST_ENTRY",
            "robot_id": self.robot_name,
            "aisle": base,
            "node": current_node,
        })
        self.emitter.send(msg.encode())
        print(f"{self.robot_name}: Toegang gevraagd aan {base}")

    def _notify_aisle_exit(self):
        # Send exited when exiting an aisle
        if self.current_locked_aisle is None:
            return
        msg = json.dumps({
            "type": "EXITING",
            "robot_id": self.robot_name,
            "aisle": self.current_locked_aisle,
        })
        self.emitter.send(msg.encode())
        print(f"{self.robot_name}: Gang {self.current_locked_aisle} verlaten")
        self.current_locked_aisle = None

    def _poll_receiver(self):
        # Poll messages from aisle devices and update self.aisle_response if relevant messages are received.
        while self.receiver.getQueueLength() > 0:
            msg = json.loads(self.receiver.getString())
            self.receiver.nextPacket()
            if msg.get("to") == self.robot_name:
                self.aisle_response = msg["type"]
                print(f"{self.robot_name}: Aisle response: {msg['type']} voor {msg.get('aisle')}")

    def _handle_obstacle(self, target_name):
        # React to a blocked path
        self._drive(0, 0)
        self.obstructed_nodes.append(target_name)
        print(f"{self.robot_name}: Obstakel bij {target_name}! Terug naar {self.current_node}")

        if self.current_locked_aisle is not None and "Aisle" not in target_name:
            self._notify_aisle_exit()

        self.route = get_route(self.nodes, self.edges, self.current_node,
                               self.obstructed_nodes, self.current_node)
        self.target_node_index = 0
        self._transition("ROTATING")

    def _on_waypoint_reached(self, target_name):
        # Handle logic when a waypoint/node is reached
        print(f"{self.robot_name}: Node {target_name} bereikt")

        if "Aisle" not in target_name and self.current_node and "Aisle" in self.current_node:
            self._notify_aisle_exit()

        self.current_node = target_name
        self.target_node_index += 1

        if self.target_node_index < len(self.route):
            self._transition("ROTATING")
        else:
            self._on_route_finished()

    def _on_route_finished(self):
        # Handle logic when the end of a route is reached
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
        drive(self.hal.left_motor, self.hal.right_motor, left_speed, right_speed,
              self.hal.lidar, self.nearby_threshold, slow_factor)


if __name__ == "__main__":
    robot = RobotController()
    robot.run()
