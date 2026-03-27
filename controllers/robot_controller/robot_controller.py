import json
import math
import os
from controller import Robot
from shortest_path import shortest_path

# Some parts of this controller are deviated from an example controller (written in c. So a different language, but the logic/implemted-steps have a big overlap):
#   https://github.com/cyberbotics/webots/blob/R2021b/projects/robots/robotis/turtlebot/controllers/turtlebot3_ostacle_avoidance/turtlebot3_ostacle_avoidance.c

# This documentation helped building the controller:
#   https://pockerman-py-cubeai.readthedocs.io/en/latest/Examples/Webots/webots_ctrl_dev_101.html

class RobotController:
    def __init__(self):
        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())

        # Settings:
        #TODO: optimize these settings
        self.max_speed = 4 # Max is 6.28
        self.dist_error = 0.05 # Meters
        self.angle_error = 0.04 # Radians

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

        # States:
        # Possible states: ROTATING, MOVING, IDLE, ... #TODO with more advanced steps later in the project (collision preventiopn etc...)
        self.state = "ROTATING"

        # Map:
        self.load_map()
        self.current_node = "Droppoff_2" # Currently this controller is for r2, which is starting on droppoff 2
        self.target_node_index = 0

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

    def get_route(self, end_node):
        self.route = shortest_path(self.nodes, self.edges, self.current_node, end_node)
        print(f"Path: {self.route}")

    def drive(self, left_speed, right_speed):
        self.left_motor.setVelocity(left_speed)
        self.right_motor.setVelocity(right_speed)

    def run(self):
        while self.robot.step(self.time_step) != -1:
            if not self.route or self.target_node_index >= len(self.route):
                print("No route or destination reached")
                #TODO: Wait for next target (node to visit), this basicly means moving to the next order... (this todo is repeated below in the FSM)
                self.state = "IDLE"
                # @HERE
                break
            
            target_name = self.route[self.target_node_index]
            target_position = self.nodes[target_name]

            position = self.gps.getValues()
            if math.isnan(position[0]) or math.isnan(position[1]): continue

            distance_x = target_position['x'] - position[0]
            # print(f"target_x: {target_position['x']}, position_x: {position[0]}") # [DEBUG]
            distance_y = target_position['y'] - position[1]
            # print(f"target_y: {target_position['y']}, position_y: {position[1]}") # [DEBUG]
            distance = math.sqrt(distance_x**2 + distance_y**2)

            target_angle = math.atan2(distance_y, distance_x)
            current_angle = self.get_direction()
            angle_diff = target_angle - current_angle
            while angle_diff > math.pi: angle_diff -= 2 * math.pi
            while angle_diff < -math.pi: angle_diff += 2 * math.pi
            # print(angle_diff) # [DEBUG]

            # FSM for the different states:
            if self.state == "ROTATING":
                if abs(angle_diff) > self.angle_error:
                    if angle_diff > 0:
                        rotate_speed = -0.8 #TODO: Fix magic numbers on top of this doc
                    else:
                        rotate_speed = 0.8 #TODO: Fix magic numbers on top of this doc
                    self.drive(rotate_speed, -rotate_speed)
                else:
                    self.state = "MOVING"
                
            elif self.state == "MOVING":
                if distance > self.dist_error:
                    driving_speed = 4.0 #TODO: Fix magic numbers on top of this doc
                    # Used Gemini (27/03/2026) to implement a correction to account for slip etc... so the robot isn't driving straigth forward blindly
                    correction = angle_diff * 3.0 #TODO: Fix magic numbers on top of this doc
                    self.drive(driving_speed - correction, driving_speed + correction)
                else:
                    print(f"Node {target_name} reached")
                    self.target_node_index += 1
                    self.state = "ROTATING"

            elif self.state == "IDLE":
                print("Idling") 
                #TODO: Implement getting new tasks, combining this movement code into a fully functioning warehouse order-picking project. (implement a warehouse with central controller)
                # @HERE

robot = RobotController()
robot.get_route("Entrance_2_4") #TODO: set route with warehouse control logic!? # @HERE
robot.run()