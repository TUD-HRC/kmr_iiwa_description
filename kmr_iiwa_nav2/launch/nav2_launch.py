import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer, Node, PushRosNamespace, SetRemap
from launch_ros.descriptions import ComposableNode
from launch.conditions import IfCondition


def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    pkg_project = get_package_share_directory('kmr_iiwa_nav2')

    slam_toolbox_launch = GroupAction(actions=[
        SetRemap(src='/tf', dst='tf'),
        SetRemap(src='/tf_static', dst='tf_static'),
        SetRemap(src='/map', dst='map'),
        SetRemap(src='/map_metadata', dst='map_metadata'),
        PushRosNamespace('kmr_iiwa'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                pkg_project + '/launch/online_async_launch.py'
            ),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'slam_params_file': os.path.join(
                    pkg_project, 'config', 'mapper_online_params_online_async.yaml'
                ),
            }.items()
        ),
    ])

    # Fuse the two SICK scans into a single 360-ish degree scan.  Slam Toolbox
    # only accepts one scan_topic, so mapper_online_params uses the "scan"
    # output of this node instead of scan_front_right.
    scan_merger = GroupAction(actions=[
        SetRemap(src='/tf', dst='tf'),
        SetRemap(src='/tf_static', dst='tf_static'),
        ComposableNodeContainer(
            package='rclcpp_components',
            executable='component_container',
            name='scan_merger_container',
            namespace='kmr_iiwa',
            composable_node_descriptions=[
                ComposableNode(
                    package='scan_2d_merger',
                    plugin='util::LaserScanMerger',
                    name='scan_2d_merger_node',
                    # Without this the component is loaded in the root
                    # namespace, so its relative topics resolve to
                    # /scan_front_right and /scan_merged instead of
                    # /kmr_iiwa/... .
                    namespace='kmr_iiwa',
                    parameters=[os.path.join(
                        pkg_project, 'config', 'scan_merger.yaml'
                    )],
                    extra_arguments=[{'use_intra_process_comms': True}],
                )
            ],
            output='screen',
        ),
    ])

    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            nav2_bringup_dir + '/launch/bringup_launch.py'
        ),
        launch_arguments={
            'namespace': 'kmr_iiwa',
            'use_namespace': 'True',
            'use_sim_time': use_sim_time,
            'use_localization': 'False',
            'use_keepout_zones': 'False',
            'use_speed_zones': 'False',
            'params_file': os.path.join(pkg_project, 'config', 'nav2_params.yaml'),
        }.items()
    )
    

    nav2_costmap_2d_markers_node = Node(
        package='nav2_costmap_2d',
        executable='nav2_costmap_2d_markers',
        namespace='kmr_iiwa',
        name='nav2_costmap_2d_markers',
        output='screen',
        parameters=[{
            'voxel_grid': '/local_costmap/voxel_grid',
            'visualization_marker': '/local_costmap/obstacle_markers'
        }],
        condition=IfCondition(LaunchConfiguration("costmap_marker")),
    )

    return LaunchDescription([
        DeclareLaunchArgument(name='use_sim_time', default_value='True', description='Flag to enable use_sim_time'),
        DeclareLaunchArgument(name='costmap_marker', default_value='False'),
        scan_merger,
        slam_toolbox_launch,
        nav2_bringup_launch,   
        nav2_costmap_2d_markers_node
    ])