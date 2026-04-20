cmake_minimum_required(VERSION 3.0.2)
project(thesis_tasks)

find_package(catkin REQUIRED COMPONENTS
  actionlib
  geometry_msgs
  move_base_msgs
  rospy
  std_msgs
  tf
)

catkin_package(
  CATKIN_DEPENDS actionlib geometry_msgs move_base_msgs rospy std_msgs tf
)

catkin_install_python(PROGRAMS
  scripts/task_manager_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
