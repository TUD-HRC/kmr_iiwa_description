# kmr_iiwa_nav2
Config and launches for ros2 nav2 stack

## Notes
Behavior server is the node controlling the varios behavior. The publishing chain is:

`BEHAVIOR_SERVER --> cmd_vel_nav --> VELOCITY_SMOOTHER --> cmd_vel_smoothed --> COLLISION_MONITOR --> /kmr_iiwa/cmd_vel --> /KMR_IIWA/BASE_VELOCITY_CONTROLLER`  

The base_velocity_controller is the one defined in the kmr_iiwa_gazebo package, which directly comunicate with the hardware/simulated gazebo plugin