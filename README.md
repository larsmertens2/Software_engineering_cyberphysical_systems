# Software Engineering Cyber-Physical Systems 

Info on how to prevent collisions:
- a robot always travels from node to node, which means it shouldn't collide with structures. 
- To prevent collisions with other bots we should have some driving rules:
* The "robot highway" is now 2x6, meaning if all robots go anticlockwise (or clockwise) they will never collide. But they should be looking if there's a robot in the node they want to go to (and wait till he moved on).
* If we expand the highway to 3x6, we need to add other rules of how to use the middle lane. We can use it as a return lane.