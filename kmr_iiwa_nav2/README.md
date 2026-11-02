# kmr_iiwa_nav2

Configuration and launch files for the ROS 2 Nav2 stack.

## Examples
Once everything the launches are launched, wanted behavior must be activate through sending an action, for example for assisted teleoperation:  

```bash
ros2 action send_goal /kmr_iiwa/assisted_teleop nav2_msgs/action/AssistedTeleop "{time_allowance: {sec: 99999, nanosec: 0}}"
```

## Notes

The behavior server is the node that controls the various navigation behaviors. The publishing chain is:

`BEHAVIOR_SERVER --> cmd_vel_nav --> VELOCITY_SMOOTHER --> cmd_vel_smoothed --> COLLISION_MONITOR --> /kmr_iiwa/cmd_vel --> /KMR_IIWA/BASE_VELOCITY_CONTROLLER`

For example, the assisted teleop behavior allows to publish at the top of the chain: 
 `cmd_vel_teleop --> BEHAVIOR_SERVER --> ...`

The `base_velocity_controller` is configured in `kmr_iiwa_urdf/config/controllers/gazebo.yaml` using the plugin from `gz_virtual_base_system`, and communicates directly with the hardware or with the simulated Gazebo plugin.

