# Software Engineering Cyber-Physical Systems 

Running the project
Setting up the project can be done with these simple steps:
Unpack the project or clone from github (https://github.com/larsmertens2/Software_engineering_cyberphysical_systems).
Get all imports with pip using the requirements.txt in the project root. Make sure to use the python version that Webots is using. Use the following command (in project root): $ py -m pip install -r requirements.txt
Start the backend api and serve the webapp by using the following command (in project root): $ docker-compose up –build. Docker desktop is required to be installed for this.
Open the warehouse.wbt file in Webots. The simulation should be ready to run.
Visit the user interface in your browser http://localhost:5173

Change the python version Webots is using by editing “Python Command” under tools → preferences in Webots (if the versions don’t match).
