# Software Engineering Cyber-Physical Systems 

Info on how to prevent collisions:
- a robot always travels from node to node, which means it shouldn't collide with structures. 
- To prevent collisions with other bots we should have some driving rules:
* The "robot highway" is now 2x6, meaning if all robots go anticlockwise (or clockwise) they will never collide. But they should be looking if there's a robot in the node they want to go to (and wait till he moved on).
* If we expand the highway to 3x6, we need to add other rules of how to use the middle lane. We can use it as a return lane.


#info about Warehouse manager:
The warehousemanager should have a taskController and a robotcontroller for each robot. The task controller should be responsible for assigning tasks to the robots, while the robot controller should be responsible for controlling the movement of the robots and ensuring they follow the driving rules to prevent collisions. At the moment are tasks given in the robotcontroller but should be move moved to the warehousemanager. the warehousemanager might also be able to keep track of all the robots and the maps as an oversight, but might add coupling if the robotcontroller needs to ask the warehousemanager for information about the map or other robots.