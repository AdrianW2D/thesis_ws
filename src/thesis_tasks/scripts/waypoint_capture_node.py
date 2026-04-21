#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import os

import yaml

import rospy
from geometry_msgs.msg import PoseStamped
from tf.transformations import euler_from_quaternion


class WaypointCaptureNode(object):
    """Capture RViz 2D Nav Goal clicks into a Task3 waypoint YAML."""

    def __init__(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_output = (
            "$HOME/thesis_ws/tasks/waypoint_sets/patrol_capture_{0}.yaml".format(
                timestamp
            )
        )

        self.output_file = self._resolve_path(
            rospy.get_param("~output_file", default_output)
        )
        self.map_id = str(rospy.get_param("~map_id", "task1_lab_v01"))
        self.frame_id = str(rospy.get_param("~frame_id", "map"))
        self.task_set_id = str(
            rospy.get_param("~task_set_id", os.path.splitext(os.path.basename(self.output_file))[0])
        )
        self.task_set_name = str(
            rospy.get_param("~task_set_name", self.task_set_id)
        )
        self.default_task_type = str(rospy.get_param("~default_task_type", "checkpoint"))
        self.default_stay_time_sec = float(rospy.get_param("~default_stay_time_sec", 1.0))
        self.auto_write = bool(rospy.get_param("~auto_write", True))
        self.points = []

        self._load_existing_file()
        self._ensure_parent_dir()

        self.goal_sub = rospy.Subscriber(
            "/move_base_simple/goal", PoseStamped, self._goal_callback, queue_size=10
        )
        rospy.on_shutdown(self._on_shutdown)

        rospy.loginfo("Waypoint capture node ready.")
        rospy.loginfo("  output_file: %s", self.output_file)
        rospy.loginfo("  map_id: %s", self.map_id)
        rospy.loginfo("  frame_id: %s", self.frame_id)
        rospy.loginfo("  existing_points: %d", len(self.points))
        rospy.loginfo(
            "Click RViz 2D Nav Goal to capture waypoint poses. The YAML will be "
            "updated after each click."
        )

    def _resolve_path(self, raw_path):
        return os.path.abspath(os.path.expanduser(os.path.expandvars(raw_path)))

    def _ensure_parent_dir(self):
        parent_dir = os.path.dirname(self.output_file)
        if parent_dir and not os.path.isdir(parent_dir):
            os.makedirs(parent_dir)

    def _load_existing_file(self):
        if not os.path.isfile(self.output_file):
            return

        try:
            with open(self.output_file, "r") as handle:
                data = yaml.safe_load(handle) or {}
        except Exception as exc:
            rospy.logwarn("Failed to load existing capture file %s: %s", self.output_file, exc)
            return

        if not isinstance(data, dict):
            rospy.logwarn("Existing capture file is not a mapping: %s", self.output_file)
            return

        self.task_set_id = str(data.get("task_set_id", self.task_set_id))
        self.task_set_name = str(data.get("task_set_name", self.task_set_name))
        self.map_id = str(data.get("map_id", self.map_id))
        self.frame_id = str(data.get("frame_id", self.frame_id))

        points = data.get("points", [])
        if isinstance(points, list):
            self.points = points

    def _format_float(self, value):
        return "{0:.4f}".format(float(value))

    def _render_yaml(self):
        lines = [
            "task_set_id: {0}".format(self.task_set_id),
            "task_set_name: {0}".format(self.task_set_name),
            "map_id: {0}".format(self.map_id),
            "frame_id: {0}".format(self.frame_id),
            "description: >",
            "  Captured from RViz 2D Nav Goal clicks for Task3 waypoint debugging.",
            "",
            "points:",
        ]

        if not self.points:
            lines[-1] = "points: []"
            return "\n".join(lines) + "\n"

        for point in self.points:
            lines.extend(
                [
                    "  - point_id: {0}".format(point["point_id"]),
                    "    point_name: {0}".format(point["point_name"]),
                    "    sequence: {0}".format(point["sequence"]),
                    "    pose:",
                    "      x: {0}".format(self._format_float(point["pose"]["x"])),
                    "      y: {0}".format(self._format_float(point["pose"]["y"])),
                    "      yaw: {0}".format(self._format_float(point["pose"]["yaw"])),
                    "    tolerance:",
                    "      xy: 0.30",
                    "      yaw_deg: 15",
                    "    task_type: {0}".format(point["task_type"]),
                    "    stay_time_sec: {0}".format(self._format_float(point["stay_time_sec"])),
                    "    expected_action: arrive_only",
                    "    enabled: true",
                    "    tags:",
                    "      - captured",
                    "      - rviz",
                    "    note: Captured from /move_base_simple/goal.",
                    "",
                ]
            )

        return "\n".join(lines)

    def _write_file(self):
        self._ensure_parent_dir()
        with open(self.output_file, "w") as handle:
            handle.write(self._render_yaml())

    def _goal_callback(self, msg):
        quaternion = [
            msg.pose.orientation.x,
            msg.pose.orientation.y,
            msg.pose.orientation.z,
            msg.pose.orientation.w,
        ]
        yaw = euler_from_quaternion(quaternion)[2]

        sequence = len(self.points) + 1
        point_id = "P{0:02d}".format(sequence)
        point_name = "captured_p{0:02d}".format(sequence)

        point = {
            "point_id": point_id,
            "point_name": point_name,
            "sequence": sequence,
            "pose": {
                "x": float(msg.pose.position.x),
                "y": float(msg.pose.position.y),
                "yaw": float(yaw),
            },
            "task_type": self.default_task_type,
            "stay_time_sec": self.default_stay_time_sec,
        }

        self.points.append(point)

        if self.auto_write:
            self._write_file()

        rospy.loginfo(
            "Captured %s seq=%d pose=(%.4f, %.4f, %.4f) -> %s",
            point_id,
            sequence,
            point["pose"]["x"],
            point["pose"]["y"],
            point["pose"]["yaw"],
            self.output_file,
        )

    def _on_shutdown(self):
        try:
            self._write_file()
            rospy.loginfo("Waypoint capture file saved to %s", self.output_file)
        except Exception as exc:
            rospy.logerr("Failed to save waypoint capture file %s: %s", self.output_file, exc)


def main():
    rospy.init_node("waypoint_capture_node")
    node = WaypointCaptureNode()
    rospy.spin()


if __name__ == "__main__":
    main()
