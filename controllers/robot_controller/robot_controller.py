import json
import math
import os
from controller import Controller

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
        self.angle_error = 0.02 # Radians

        # Motors
        self.left_motor = self.robot.getDevice("left wheel motor")
        self.left_motor.setPosition(float('inf'))

        self.right_motor = self.robot.getDevice("right wheel motor")
        self.right_motor.setPosition(float('inf'))

        # Sensors
        self.gps = self.robot.getDevice("gps")
        self.gps.enable(self.time_step)

        self.compass = self.robot.getDevice("compass")
        self.compass.enable(self.time_step)

        # States:
        # Possible states: ROTATING, MOVING, ... #TODO with more advanced steps later in the project (collision preventiopn etc...)
        self.state = "ROTATING"

        # Map:
        self.load_map()
        self.target_node_index = 0

    def load_map(self):
        data_path = os.path.join(os.path.dirname(__file__), "map.json")
        with open(data_path, "r") as f:
            data = json.load(f)
            self.nodes = data["nodes"]
            self.edges = data["edges"]

    def get_direction(self):
        direction = self.compass.getValues()
        radians = math.atan2(direction[0], direction[2])
        return radians

    def run(self):
        print("unfinished run code")
        while self.robot.step(self.time_step) != -1:
            print("do smt")
            #TODO: implement main function of robot

robot = RobotController()
robot.run()