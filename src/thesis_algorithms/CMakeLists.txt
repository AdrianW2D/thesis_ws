cmake_minimum_required(VERSION 3.0.2)
project(thesis_algorithms)

find_package(catkin REQUIRED COMPONENTS
  rospy
  sensor_msgs
)

catkin_package(
  CATKIN_DEPENDS rospy sensor_msgs
)

catkin_install_python(PROGRAMS
  scripts/scan_enhancer_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
