# kmr_iiwa_description

ROS 2 description files for the KUKA Mobile Robot Base (MRB, standalone version called KMP 200) with an LBR iiwa arm.

The repository contains the URDF and description of the mobile base. The arm is integrated from [lbr_iiwa14_r820_description](https://github.com/lbr-stack/lbr_iiwa14_r820_description), and the ROS 2 controller configuration for the URDF comes from [lbr_fri_ros2_stack/lbr_ros2_control](https://github.com/lbr-stack/lbr_fri_ros2_stack/tree/jazzy/lbr_ros2_control).

Tested on ROS 2 Jazzy.

For use on the real robot, see https://github.com/TUD-HRC/kmr_iiwa_ros2.

## Packages

- `kmr_iiwa_urdf`: URDF/xacro files, meshes and controller configuration for the KMP 200 base and the arm.
- `kmr_iiwa_gazebo`: Gazebo simulation, including the world, the simulated robot description and the virtual base driver.
- `kmr_iiwa_nav2`: Nav2 and slam_toolbox configuration and launch files.

## Requirements

- [lbr_iiwa14_r820_description](https://github.com/lbr-stack/lbr_iiwa14_r820_description) - arm description.
- [gz_virtual_base_system](https://github.com/TUD-HRC/gz_virtual_base_system) - virtual base hardware interface used by `kmr_iiwa_gazebo`.
- [lbr_ros2_control](https://github.com/lbr-stack/lbr_fri_ros2_stack) - arm controllers used by `kmr_iiwa_gazebo`.
- [ROS 2 Nav2](https://docs.nav2.org/) - used by `kmr_iiwa_nav2`.

## Usage

```bash
# Visualize the robot model in RViz
ros2 launch kmr_iiwa_urdf rviz.launch.py

# Start the Gazebo simulation
ros2 launch kmr_iiwa_gazebo kmr_iiwa.launch.py

# Start Nav2 and slam_toolbox (Gazebo must be running)
ros2 launch kmr_iiwa_nav2 nav2_launch.py
```

## Notes

### Mobile base description

The meshes and URDF for the KMP 200, i.e. the mobile base part of the KMR iiwa, were taken from https://github.com/kidpaul94/kmr-iiwa-gripkit-cr-plus-l/tree/main and are kept here so that the mobile base has its own package.

### Arm description

Geometry, kinematics, meshes and ROS 2 controllers were taken from what should be the official sources:

- https://github.com/lbr-stack/lbr_fri_ros2_stack/tree/582fbb06d0b964f1a6fc49fe48c6ee132c0d8b9f/lbr_description/urdf/iiwa14
- https://github.com/lbr-stack/lbr_iiwa14_r820_description

### Useful commands

#### Controllers

```bash
ros2 control switch_controllers --activate joint_trajectory_controller --deactivate forward_position_controller -c /kmr_iiwa/controller_manager
ros2 control list_controllers -c /kmr_iiwa/controller_manager
```

#### Others

```bash
ros2 run topic_tools relay /kmr_iiwa/robot_description /robot_description
ros2 run rqt_joint_trajectory_controller rqt_joint_trajectory_controller
```
