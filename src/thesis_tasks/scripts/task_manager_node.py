#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import math
import os
import time
import traceback

import actionlib
import yaml

import rospy
from geometry_msgs.msg import PoseWithCovarianceStamped
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from tf.transformations import euler_from_quaternion, quaternion_from_euler


GOAL_STATUS_NAMES = {
    0: "PENDING",
    1: "ACTIVE",
    2: "PREEMPTED",
    3: "SUCCEEDED",
    4: "ABORTED",
    5: "REJECTED",
    6: "PREEMPTING",
    7: "RECALLING",
    8: "RECALLED",
    9: "LOST",
}


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def _normalize_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


class TaskManager(object):
    """Task execution manager for line2 navigation execution experiments."""

    def __init__(self):
        self.state = "INIT"
        self.task_file = self._resolve_path(
            rospy.get_param(
                "~task_file",
                "$HOME/thesis_ws/tasks/waypoint_sets/patrol_smoke_v01.yaml",
            )
        )
        self.result_dir = self._resolve_path(
            rospy.get_param("~result_dir", "$HOME/thesis_ws/results/patrol")
        )
        self.session_label = str(rospy.get_param("~session_label", "patrol")).strip()
        if not self.session_label:
            self.session_label = "patrol"

        self.retry_limit = int(rospy.get_param("~retry_limit", 2))
        self.goal_timeout = float(rospy.get_param("~goal_timeout", 60.0))
        self.skip_on_failure = _as_bool(rospy.get_param("~skip_on_failure", True))
        self.ready_timeout = float(rospy.get_param("~ready_timeout", 30.0))

        self.execution_mode = str(rospy.get_param("~execution_mode", "enhanced")).strip().lower()
        if self.execution_mode not in ("baseline", "enhanced"):
            rospy.logwarn(
                "Unknown execution_mode '%s'. Falling back to 'enhanced'.",
                self.execution_mode,
            )
            self.execution_mode = "enhanced"

        default_two_stage = self.execution_mode == "enhanced"
        default_progress_monitor = self.execution_mode == "enhanced"
        default_thesis_acceptance = self.execution_mode == "enhanced"

        self.enable_two_stage_goal = _as_bool(
            rospy.get_param("~enable_two_stage_goal", default_two_stage)
        )
        self.enable_progress_monitor = _as_bool(
            rospy.get_param("~enable_progress_monitor", default_progress_monitor)
        )
        self.enable_thesis_acceptance = _as_bool(
            rospy.get_param("~enable_thesis_acceptance", default_thesis_acceptance)
        )
        self.progress_timeout = float(rospy.get_param("~progress_timeout", 12.0))
        self.stall_check_interval = max(
            0.1, float(rospy.get_param("~stall_check_interval", 0.5))
        )
        self.min_progress_delta = float(rospy.get_param("~min_progress_delta", 0.08))
        self.coarse_goal_timeout_ratio = float(
            rospy.get_param("~coarse_goal_timeout_ratio", 0.60)
        )
        self.coarse_xy_tolerance = float(
            rospy.get_param("~coarse_xy_tolerance", 0.45)
        )
        self.write_yaml_summary = _as_bool(
            rospy.get_param("~write_yaml_summary", True)
        )

        self.session_started_at = datetime.datetime.now()
        self.session_id = "{0}_{1}".format(
            self.session_label,
            self.session_started_at.strftime("%Y%m%d_%H%M%S"),
        )
        self.summary_path = os.path.join(self.result_dir, self.session_id + ".md")
        self.summary_yaml_path = os.path.join(self.result_dir, self.session_id + ".yaml")

        self.task_set_id = ""
        self.task_set_name = ""
        self.map_id = ""
        self.frame_id = "map"
        self.raw_task = None
        self.task_points = []
        self.current_index = -1
        self.current_goal = None
        self.latest_amcl_pose_msg = None
        self.session_records = []
        self.mission_status = "INIT"
        self.abort_reason = ""
        self.session_finished_at = None
        self.goal_active = False

        self.metrics = {
            "waypoint_total": 0,
            "waypoint_completed": 0,
            "waypoint_skipped": 0,
            "waypoint_failed": 0,
            "retry_count": 0,
            "timeout_count": 0,
            "stall_count": 0,
            "recovery_trigger_count": 0,
            "accepted_by_thesis_count": 0,
        }

        self.move_base_client = actionlib.SimpleActionClient(
            "move_base", MoveBaseAction
        )
        self.amcl_subscriber = rospy.Subscriber(
            "/amcl_pose",
            PoseWithCovarianceStamped,
            self._amcl_pose_callback,
            queue_size=10,
        )

        rospy.on_shutdown(self._on_shutdown)

    def _resolve_path(self, raw_path):
        return os.path.abspath(os.path.expanduser(os.path.expandvars(raw_path)))

    def _ensure_result_dir(self):
        if not os.path.isdir(self.result_dir):
            os.makedirs(self.result_dir)

    def _on_shutdown(self):
        if self.goal_active:
            rospy.logwarn("Shutdown requested. Canceling active move_base goal.")
            try:
                self.move_base_client.cancel_all_goals()
            except Exception:
                pass

    def _amcl_pose_callback(self, msg):
        self.latest_amcl_pose_msg = msg

    def _pose_from_amcl(self):
        if self.latest_amcl_pose_msg is None:
            return None

        pose = self.latest_amcl_pose_msg.pose.pose
        quaternion = (
            pose.orientation.x,
            pose.orientation.y,
            pose.orientation.z,
            pose.orientation.w,
        )
        yaw = euler_from_quaternion(quaternion)[2]
        return {
            "x": pose.position.x,
            "y": pose.position.y,
            "yaw": yaw,
        }

    def _compute_pose_errors(self, target_pose):
        current_pose = self._pose_from_amcl()
        if current_pose is None:
            return {
                "distance": None,
                "yaw_error_deg": None,
                "current_pose": None,
            }

        dx = target_pose["x"] - current_pose["x"]
        dy = target_pose["y"] - current_pose["y"]
        distance = math.sqrt(dx * dx + dy * dy)
        yaw_error = math.degrees(
            abs(_normalize_angle(target_pose["yaw"] - current_pose["yaw"]))
        )
        return {
            "distance": distance,
            "yaw_error_deg": yaw_error,
            "current_pose": current_pose,
        }

    def _goal_state_name(self, goal_state):
        return GOAL_STATUS_NAMES.get(goal_state, "UNKNOWN_{0}".format(goal_state))

    def _build_move_base_goal(self, target_pose):
        quaternion = quaternion_from_euler(0.0, 0.0, target_pose["yaw"])
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = self.frame_id
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose.position.x = target_pose["x"]
        goal.target_pose.pose.position.y = target_pose["y"]
        goal.target_pose.pose.position.z = 0.0
        goal.target_pose.pose.orientation.x = quaternion[0]
        goal.target_pose.pose.orientation.y = quaternion[1]
        goal.target_pose.pose.orientation.z = quaternion[2]
        goal.target_pose.pose.orientation.w = quaternion[3]
        return goal

    def _require_mapping(self, value, field_name):
        if not isinstance(value, dict):
            raise ValueError("Field '{0}' must be a mapping".format(field_name))
        return value

    def _require_field(self, mapping, field_name, context_name):
        if field_name not in mapping:
            raise ValueError(
                "Missing required field '{0}' in {1}".format(field_name, context_name)
            )
        return mapping[field_name]

    def _require_float(self, value, field_name, context_name):
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError(
                "Field '{0}' in {1} must be numeric".format(field_name, context_name)
            )

    def log_configuration(self):
        rospy.loginfo("Task manager session: %s", self.session_id)
        rospy.loginfo("  task_file: %s", self.task_file)
        rospy.loginfo("  result_dir: %s", self.result_dir)
        rospy.loginfo("  execution_mode: %s", self.execution_mode)
        rospy.loginfo("  retry_limit: %d", self.retry_limit)
        rospy.loginfo("  goal_timeout: %.1f", self.goal_timeout)
        rospy.loginfo("  skip_on_failure: %s", self.skip_on_failure)
        rospy.loginfo("  ready_timeout: %.1f", self.ready_timeout)
        rospy.loginfo("  enable_two_stage_goal: %s", self.enable_two_stage_goal)
        rospy.loginfo("  enable_progress_monitor: %s", self.enable_progress_monitor)
        rospy.loginfo("  enable_thesis_acceptance: %s", self.enable_thesis_acceptance)
        rospy.loginfo("  progress_timeout: %.1f", self.progress_timeout)
        rospy.loginfo("  coarse_xy_tolerance: %.2f", self.coarse_xy_tolerance)
        rospy.loginfo("  summary_path: %s", self.summary_path)

    def _parse_point(self, raw_point, default_sequence, raw_index):
        context_name = "point[{0}]".format(raw_index)
        point = self._require_mapping(raw_point, context_name)

        enabled = _as_bool(point.get("enabled", False))
        if not enabled:
            return None

        point_id = self._require_field(point, "point_id", context_name)
        point_name = self._require_field(point, "point_name", context_name)
        task_type = self._require_field(point, "task_type", context_name)
        pose = self._require_mapping(
            self._require_field(point, "pose", context_name),
            "{0}.pose".format(context_name),
        )

        sequence = point.get("sequence", default_sequence)
        try:
            sequence = int(sequence)
        except (TypeError, ValueError):
            raise ValueError(
                "Field 'sequence' in {0} must be an integer".format(context_name)
            )

        tolerance = point.get("tolerance", {}) or {}
        if tolerance and not isinstance(tolerance, dict):
            raise ValueError(
                "Field 'tolerance' in {0} must be a mapping".format(context_name)
            )

        return {
            "point_id": point_id,
            "point_name": point_name,
            "sequence": sequence,
            "task_type": task_type,
            "enabled": enabled,
            "pose": {
                "x": self._require_float(
                    self._require_field(pose, "x", "{0}.pose".format(context_name)),
                    "pose.x",
                    context_name,
                ),
                "y": self._require_float(
                    self._require_field(pose, "y", "{0}.pose".format(context_name)),
                    "pose.y",
                    context_name,
                ),
                "yaw": self._require_float(
                    self._require_field(pose, "yaw", "{0}.pose".format(context_name)),
                    "pose.yaw",
                    context_name,
                ),
            },
            "tolerance": {
                "xy": float(tolerance.get("xy", 0.30)),
                "yaw_deg": float(tolerance.get("yaw_deg", 15.0)),
            },
            "stay_time_sec": float(point.get("stay_time_sec", 0.0)),
            "expected_action": point.get("expected_action", ""),
            "note": point.get("note", ""),
            "raw_index": raw_index,
        }

    def load_task(self):
        self.state = "LOAD_TASK"

        if not os.path.isfile(self.task_file):
            rospy.logerr("Task file does not exist: %s", self.task_file)
            return False

        try:
            with open(self.task_file, "r") as handle:
                self.raw_task = yaml.safe_load(handle) or {}
        except (IOError, OSError) as exc:
            rospy.logerr("Failed to open task file %s: %s", self.task_file, exc)
            return False
        except yaml.YAMLError as exc:
            rospy.logerr("Failed to parse YAML %s: %s", self.task_file, exc)
            return False

        if not isinstance(self.raw_task, dict):
            rospy.logerr("Task file must contain a top-level mapping: %s", self.task_file)
            return False

        try:
            self.task_set_id = self._require_field(
                self.raw_task, "task_set_id", "task file"
            )
            self.task_set_name = self._require_field(
                self.raw_task, "task_set_name", "task file"
            )
            self.map_id = str(self._require_field(self.raw_task, "map_id", "task file"))
            self.frame_id = str(
                self._require_field(self.raw_task, "frame_id", "task file")
            )
            raw_points = self._require_field(self.raw_task, "points", "task file")
            if not isinstance(raw_points, list):
                raise ValueError("Field 'points' in task file must be a list")

            parsed_points = []
            for raw_index, raw_point in enumerate(raw_points):
                parsed = self._parse_point(
                    raw_point, default_sequence=raw_index + 1, raw_index=raw_index
                )
                if parsed is not None:
                    parsed_points.append(parsed)

            parsed_points.sort(key=lambda item: (item["sequence"], item["raw_index"]))
            self.task_points = parsed_points
            self.metrics["waypoint_total"] = len(self.task_points)
        except ValueError as exc:
            rospy.logerr("Invalid task file %s: %s", self.task_file, exc)
            return False

        if not self.task_points:
            rospy.logerr("No enabled waypoints found in task file: %s", self.task_file)
            return False

        rospy.loginfo(
            "Loaded task metadata from %s with keys: %s",
            self.task_file,
            sorted(self.raw_task.keys()),
        )
        rospy.loginfo(
            "Task set: id=%s name=%s map_id=%s frame_id=%s enabled_points=%d",
            self.task_set_id,
            self.task_set_name,
            self.map_id,
            self.frame_id,
            len(self.task_points),
        )
        if not self.map_id:
            rospy.logwarn("Task file map_id is empty. Execution does not block on it.")

        for point in self.task_points:
            rospy.loginfo(
                "  loaded waypoint seq=%d id=%s name=%s pose=(%.3f, %.3f, %.3f)",
                point["sequence"],
                point["point_id"],
                point["point_name"],
                point["pose"]["x"],
                point["pose"]["y"],
                point["pose"]["yaw"],
            )

        return True

    def wait_until_ready(self):
        self.state = "WAIT_READY"
        start_time = time.time()

        rospy.loginfo(
            "Waiting for /move_base action server (timeout: %.1fs)",
            self.ready_timeout,
        )
        if not self.move_base_client.wait_for_server(
            rospy.Duration.from_sec(self.ready_timeout)
        ):
            rospy.logerr(
                "Timed out waiting for /move_base action server after %.1fs",
                self.ready_timeout,
            )
            return False

        elapsed = time.time() - start_time
        remaining_timeout = max(0.0, self.ready_timeout - elapsed)
        if remaining_timeout <= 0.0:
            rospy.logerr("Ready timeout exhausted before waiting for /amcl_pose")
            return False

        rospy.loginfo(
            "Received /move_base action server. Waiting for first /amcl_pose "
            "(remaining timeout: %.1fs)",
            remaining_timeout,
        )
        try:
            self.latest_amcl_pose_msg = rospy.wait_for_message(
                "/amcl_pose",
                PoseWithCovarianceStamped,
                timeout=remaining_timeout,
            )
        except rospy.ROSException:
            rospy.logerr(
                "Timed out waiting for /amcl_pose after %.1fs total ready window",
                self.ready_timeout,
            )
            return False

        current_pose = self._pose_from_amcl()
        rospy.loginfo(
            "Ready gate passed. First /amcl_pose received at (%.3f, %.3f)",
            current_pose["x"],
            current_pose["y"],
        )
        return True

    def select_target(self):
        self.state = "SELECT_TARGET"
        next_index = self.current_index + 1
        if next_index >= len(self.task_points):
            rospy.loginfo("Reached end of task queue.")
            return None

        self.current_index = next_index
        self.current_goal = self.task_points[self.current_index]
        rospy.loginfo(
            "Selected waypoint %d/%d: seq=%d id=%s name=%s",
            self.current_index + 1,
            len(self.task_points),
            self.current_goal["sequence"],
            self.current_goal["point_id"],
            self.current_goal["point_name"],
        )
        return self.current_goal

    def _build_stage_plan(self, target):
        direct_stage = {
            "stage_name": "direct",
            "goal_pose": dict(target["pose"]),
            "goal_timeout": self.goal_timeout,
            "accept_xy_tolerance": target["tolerance"]["xy"],
            "accept_yaw_tolerance_deg": target["tolerance"]["yaw_deg"],
        }

        if self.execution_mode != "enhanced" or not self.enable_two_stage_goal:
            return [direct_stage]

        current_pose = self._pose_from_amcl()
        approach_yaw = target["pose"]["yaw"]
        if current_pose is not None:
            approach_yaw = current_pose["yaw"]

        approach_stage = {
            "stage_name": "approach",
            "goal_pose": {
                "x": target["pose"]["x"],
                "y": target["pose"]["y"],
                "yaw": approach_yaw,
            },
            "goal_timeout": max(5.0, self.goal_timeout * self.coarse_goal_timeout_ratio),
            "accept_xy_tolerance": max(
                target["tolerance"]["xy"], self.coarse_xy_tolerance
            ),
            "accept_yaw_tolerance_deg": 180.0,
        }
        align_stage = {
            "stage_name": "align",
            "goal_pose": dict(target["pose"]),
            "goal_timeout": self.goal_timeout,
            "accept_xy_tolerance": target["tolerance"]["xy"],
            "accept_yaw_tolerance_deg": target["tolerance"]["yaw_deg"],
        }
        return [approach_stage, align_stage]

    def send_goal(self, stage):
        self.state = "SEND_GOAL"
        goal = self._build_move_base_goal(stage["goal_pose"])
        self.move_base_client.send_goal(goal)
        self.goal_active = True

        rospy.loginfo(
            "Sent move_base goal: stage=%s frame=%s pose=(%.3f, %.3f, %.3f)",
            stage["stage_name"],
            self.frame_id,
            stage["goal_pose"]["x"],
            stage["goal_pose"]["y"],
            stage["goal_pose"]["yaw"],
        )
        return {
            "sent_at": time.time(),
            "goal_frame_id": self.frame_id,
        }

    def wait_for_goal_result(self, stage):
        self.state = "WAIT_RESULT"
        start_time = time.time()
        last_progress_time = start_time
        progress_distance = None
        best_distance = None

        initial_errors = self._compute_pose_errors(stage["goal_pose"])
        if initial_errors["distance"] is not None:
            progress_distance = initial_errors["distance"]
            best_distance = initial_errors["distance"]

        rospy.loginfo(
            "Waiting for move_base result: stage=%s timeout=%.1fs progress_monitor=%s",
            stage["stage_name"],
            stage["goal_timeout"],
            self.enable_progress_monitor,
        )

        while not rospy.is_shutdown():
            if self.move_base_client.wait_for_result(
                rospy.Duration.from_sec(self.stall_check_interval)
            ):
                self.goal_active = False
                goal_state = self.move_base_client.get_state()
                return {
                    "timed_out": False,
                    "stalled": False,
                    "goal_state": goal_state,
                    "goal_state_name": self._goal_state_name(goal_state),
                    "status_text": self.move_base_client.get_goal_status_text(),
                    "finished_at": time.time(),
                    "best_distance": best_distance,
                    "pose_errors": self._compute_pose_errors(stage["goal_pose"]),
                }

            elapsed = time.time() - start_time
            pose_errors = self._compute_pose_errors(stage["goal_pose"])
            current_distance = pose_errors["distance"]
            if current_distance is not None:
                if best_distance is None or current_distance < best_distance:
                    best_distance = current_distance
                if (
                    progress_distance is None
                    or (progress_distance - current_distance) >= self.min_progress_delta
                ):
                    progress_distance = current_distance
                    last_progress_time = time.time()

            if elapsed >= stage["goal_timeout"]:
                rospy.logwarn(
                    "move_base result timed out after %.1fs for stage %s. Canceling goal.",
                    stage["goal_timeout"],
                    stage["stage_name"],
                )
                self.move_base_client.cancel_goal()
                self.goal_active = False
                rospy.sleep(0.2)
                goal_state = self.move_base_client.get_state()
                return {
                    "timed_out": True,
                    "stalled": False,
                    "goal_state": goal_state,
                    "goal_state_name": self._goal_state_name(goal_state),
                    "status_text": self.move_base_client.get_goal_status_text(),
                    "finished_at": time.time(),
                    "best_distance": best_distance,
                    "pose_errors": self._compute_pose_errors(stage["goal_pose"]),
                }

            if (
                self.execution_mode == "enhanced"
                and self.enable_progress_monitor
                and current_distance is not None
                and (time.time() - last_progress_time) >= self.progress_timeout
            ):
                rospy.logwarn(
                    "Detected progress stall on stage %s after %.1fs without %.2fm "
                    "improvement. Canceling goal.",
                    stage["stage_name"],
                    self.progress_timeout,
                    self.min_progress_delta,
                )
                self.move_base_client.cancel_goal()
                self.goal_active = False
                rospy.sleep(0.2)
                goal_state = self.move_base_client.get_state()
                return {
                    "timed_out": False,
                    "stalled": True,
                    "goal_state": goal_state,
                    "goal_state_name": self._goal_state_name(goal_state),
                    "status_text": self.move_base_client.get_goal_status_text(),
                    "finished_at": time.time(),
                    "best_distance": best_distance,
                    "pose_errors": self._compute_pose_errors(stage["goal_pose"]),
                }

        self.goal_active = False
        return {
            "timed_out": False,
            "stalled": False,
            "goal_state": 9,
            "goal_state_name": self._goal_state_name(9),
            "status_text": "ROS shutdown before move_base finished",
            "finished_at": time.time(),
            "best_distance": best_distance,
            "pose_errors": self._compute_pose_errors(stage["goal_pose"]),
        }

    def _is_stage_accepted(self, stage, pose_errors):
        if not self.enable_thesis_acceptance:
            return False

        if not pose_errors or pose_errors["distance"] is None:
            return False

        if pose_errors["distance"] > stage["accept_xy_tolerance"]:
            return False

        yaw_tolerance = stage["accept_yaw_tolerance_deg"]
        if yaw_tolerance is None:
            return True

        if pose_errors["yaw_error_deg"] is None:
            return False

        return pose_errors["yaw_error_deg"] <= yaw_tolerance

    def handle_result(self, stage, attempt_index, dispatch_result, wait_result):
        self.state = "HANDLE_RESULT"
        duration_sec = max(0.0, wait_result["finished_at"] - dispatch_result["sent_at"])
        pose_errors = wait_result.get("pose_errors") or {}

        if wait_result["timed_out"]:
            attempt_status = "timeout"
            success = False
        elif wait_result["stalled"]:
            attempt_status = "stalled"
            success = False
        elif wait_result["goal_state"] == 3:
            attempt_status = "succeeded"
            success = True
        else:
            attempt_status = wait_result["goal_state_name"].lower()
            success = False

        accepted_by_thesis = False
        if not success and self._is_stage_accepted(stage, pose_errors):
            attempt_status = "accepted_by_thesis"
            success = True
            accepted_by_thesis = True
            self.metrics["accepted_by_thesis_count"] += 1

        if wait_result["timed_out"]:
            self.metrics["timeout_count"] += 1
        if wait_result["stalled"]:
            self.metrics["stall_count"] += 1

        attempt_record = {
            "attempt_index": attempt_index,
            "stage_name": stage["stage_name"],
            "status": attempt_status,
            "success": success,
            "accepted_by_thesis": accepted_by_thesis,
            "timed_out": wait_result["timed_out"],
            "stalled": wait_result["stalled"],
            "goal_state": wait_result["goal_state"],
            "goal_state_name": wait_result["goal_state_name"],
            "status_text": wait_result["status_text"],
            "duration_sec": duration_sec,
            "goal_frame_id": dispatch_result["goal_frame_id"],
            "best_distance_m": wait_result.get("best_distance"),
            "final_position_error_m": pose_errors.get("distance"),
            "final_yaw_error_deg": pose_errors.get("yaw_error_deg"),
        }

        rospy.loginfo(
            "Stage attempt finished: stage=%s attempt=%d status=%s "
            "goal_state=%s duration=%.2fs dist_err=%s yaw_err=%s",
            stage["stage_name"],
            attempt_index,
            attempt_record["status"],
            attempt_record["goal_state_name"],
            attempt_record["duration_sec"],
            (
                "{0:.3f}".format(attempt_record["final_position_error_m"])
                if attempt_record["final_position_error_m"] is not None
                else "n/a"
            ),
            (
                "{0:.2f}".format(attempt_record["final_yaw_error_deg"])
                if attempt_record["final_yaw_error_deg"] is not None
                else "n/a"
            ),
        )
        return success, attempt_record

    def execute_stage(self, stage):
        max_attempts = self.retry_limit + 1
        stage_record = {
            "stage_name": stage["stage_name"],
            "goal_pose": dict(stage["goal_pose"]),
            "goal_timeout": stage["goal_timeout"],
            "accept_xy_tolerance": stage["accept_xy_tolerance"],
            "accept_yaw_tolerance_deg": stage["accept_yaw_tolerance_deg"],
            "attempts": [],
            "attempts_used": 0,
            "final_status": "not_started",
            "final_goal_state_name": "",
            "final_status_text": "",
        }

        for attempt_index in range(1, max_attempts + 1):
            dispatch_result = self.send_goal(stage)
            wait_result = self.wait_for_goal_result(stage)
            success, attempt_record = self.handle_result(
                stage, attempt_index, dispatch_result, wait_result
            )

            stage_record["attempts"].append(attempt_record)
            stage_record["attempts_used"] = attempt_index
            stage_record["final_status"] = attempt_record["status"]
            stage_record["final_goal_state_name"] = attempt_record["goal_state_name"]
            stage_record["final_status_text"] = attempt_record["status_text"]

            if success:
                return True, stage_record

            if attempt_index < max_attempts:
                self.metrics["retry_count"] += 1
                self.metrics["recovery_trigger_count"] += 1
                rospy.logwarn(
                    "Retrying stage %s (%d/%d)",
                    stage["stage_name"],
                    attempt_index + 1,
                    max_attempts,
                )

        return False, stage_record

    def execute_target(self, target):
        stage_plan = self._build_stage_plan(target)
        waypoint_record = {
            "sequence": target["sequence"],
            "point_id": target["point_id"],
            "point_name": target["point_name"],
            "task_type": target["task_type"],
            "pose": dict(target["pose"]),
            "tolerance": dict(target["tolerance"]),
            "execution_mode": self.execution_mode,
            "stages": [],
            "attempts_used": 0,
            "final_status": "not_started",
            "final_goal_state_name": "",
            "final_status_text": "",
            "final_position_error_m": None,
            "final_yaw_error_deg": None,
        }

        for stage in stage_plan:
            rospy.loginfo(
                "Executing waypoint seq=%d id=%s stage=%s",
                target["sequence"],
                target["point_id"],
                stage["stage_name"],
            )
            stage_success, stage_record = self.execute_stage(stage)
            waypoint_record["stages"].append(stage_record)
            waypoint_record["attempts_used"] += stage_record["attempts_used"]

            if not stage_success:
                final_errors = self._compute_pose_errors(target["pose"])
                waypoint_record["final_status"] = "failed_on_{0}".format(
                    stage["stage_name"]
                )
                waypoint_record["final_goal_state_name"] = stage_record[
                    "final_goal_state_name"
                ]
                waypoint_record["final_status_text"] = stage_record["final_status_text"]
                waypoint_record["final_position_error_m"] = final_errors["distance"]
                waypoint_record["final_yaw_error_deg"] = final_errors["yaw_error_deg"]
                return False, waypoint_record

        final_errors = self._compute_pose_errors(target["pose"])
        waypoint_record["final_status"] = "succeeded"
        if waypoint_record["stages"]:
            waypoint_record["final_goal_state_name"] = waypoint_record["stages"][-1][
                "final_goal_state_name"
            ]
            waypoint_record["final_status_text"] = waypoint_record["stages"][-1][
                "final_status_text"
            ]
        waypoint_record["final_position_error_m"] = final_errors["distance"]
        waypoint_record["final_yaw_error_deg"] = final_errors["yaw_error_deg"]

        if target["stay_time_sec"] > 0.0:
            rospy.loginfo(
                "Waypoint seq=%d id=%s reached. Staying for %.1fs",
                target["sequence"],
                target["point_id"],
                target["stay_time_sec"],
            )
            rospy.sleep(target["stay_time_sec"])

        return True, waypoint_record

    def _mission_status_after_loop(self):
        if rospy.is_shutdown():
            return "INTERRUPTED"

        if self.metrics["waypoint_failed"] > 0 and not self.skip_on_failure:
            return "FAILED"

        if self.metrics["waypoint_skipped"] > 0:
            return "COMPLETED_WITH_SKIPS"

        return "COMPLETED"

    def write_summary(self):
        lines = [
            "# Patrol Session Summary",
            "",
            "- session_id: {0}".format(self.session_id),
            "- session_label: {0}".format(self.session_label),
            "- mission_status: {0}".format(self.mission_status),
            "- task_file: {0}".format(self.task_file),
            "- task_set_id: {0}".format(self.task_set_id or ""),
            "- task_set_name: {0}".format(self.task_set_name or ""),
            "- map_id: {0}".format(self.map_id or ""),
            "- frame_id: {0}".format(self.frame_id or ""),
            "- execution_mode: {0}".format(self.execution_mode),
            "- enable_two_stage_goal: {0}".format(self.enable_two_stage_goal),
            "- enable_progress_monitor: {0}".format(self.enable_progress_monitor),
            "- enable_thesis_acceptance: {0}".format(self.enable_thesis_acceptance),
            "- started_at: {0}".format(self.session_started_at.isoformat()),
            "- finished_at: {0}".format(
                self.session_finished_at.isoformat()
                if self.session_finished_at
                else ""
            ),
            "- retry_limit: {0}".format(self.retry_limit),
            "- goal_timeout: {0}".format(self.goal_timeout),
            "- progress_timeout: {0}".format(self.progress_timeout),
            "- skip_on_failure: {0}".format(self.skip_on_failure),
            "- waypoint_total: {0}".format(self.metrics["waypoint_total"]),
            "- waypoint_completed: {0}".format(self.metrics["waypoint_completed"]),
            "- waypoint_skipped: {0}".format(self.metrics["waypoint_skipped"]),
            "- waypoint_failed: {0}".format(self.metrics["waypoint_failed"]),
            "- retry_count: {0}".format(self.metrics["retry_count"]),
            "- timeout_count: {0}".format(self.metrics["timeout_count"]),
            "- stall_count: {0}".format(self.metrics["stall_count"]),
            "- recovery_trigger_count: {0}".format(
                self.metrics["recovery_trigger_count"]
            ),
            "- accepted_by_thesis_count: {0}".format(
                self.metrics["accepted_by_thesis_count"]
            ),
            "- summary_yaml_path: {0}".format(self.summary_yaml_path),
        ]

        if self.abort_reason:
            lines.append("- abort_reason: {0}".format(self.abort_reason))

        lines.extend(["", "## Waypoint Results", ""])

        if not self.session_records:
            lines.append("- No waypoint execution records were produced.")
        else:
            for record in self.session_records:
                lines.extend(
                    [
                        "### {0} {1}".format(
                            record["point_id"], record["point_name"]
                        ),
                        "",
                        "- sequence: {0}".format(record["sequence"]),
                        "- task_type: {0}".format(record["task_type"]),
                        "- final_status: {0}".format(record["final_status"]),
                        "- attempts_used: {0}".format(record["attempts_used"]),
                        "- final_goal_state: {0}".format(
                            record["final_goal_state_name"]
                        ),
                        "- final_status_text: {0}".format(
                            record["final_status_text"] or ""
                        ),
                        "- final_position_error_m: {0}".format(
                            (
                                "{0:.3f}".format(record["final_position_error_m"])
                                if record["final_position_error_m"] is not None
                                else ""
                            )
                        ),
                        "- final_yaw_error_deg: {0}".format(
                            (
                                "{0:.2f}".format(record["final_yaw_error_deg"])
                                if record["final_yaw_error_deg"] is not None
                                else ""
                            )
                        ),
                        "- pose: ({0:.3f}, {1:.3f}, {2:.3f})".format(
                            record["pose"]["x"],
                            record["pose"]["y"],
                            record["pose"]["yaw"],
                        ),
                        "",
                    ]
                )
                for stage in record["stages"]:
                    lines.extend(
                        [
                            "#### Stage {0}".format(stage["stage_name"]),
                            "",
                            "- final_status: {0}".format(stage["final_status"]),
                            "- attempts_used: {0}".format(stage["attempts_used"]),
                            "- stage_goal_pose: ({0:.3f}, {1:.3f}, {2:.3f})".format(
                                stage["goal_pose"]["x"],
                                stage["goal_pose"]["y"],
                                stage["goal_pose"]["yaw"],
                            ),
                            "- stage_accept_xy_tolerance: {0:.3f}".format(
                                stage["accept_xy_tolerance"]
                            ),
                            "- stage_accept_yaw_tolerance_deg: {0:.2f}".format(
                                stage["accept_yaw_tolerance_deg"]
                            ),
                            "",
                            "Attempts:",
                        ]
                    )
                    for attempt in stage["attempts"]:
                        lines.append(
                            "- attempt {0}: status={1}, accepted_by_thesis={2}, "
                            "goal_state={3}, duration={4:.2f}s, dist_err={5}, "
                            "yaw_err={6}, text={7}".format(
                                attempt["attempt_index"],
                                attempt["status"],
                                attempt["accepted_by_thesis"],
                                attempt["goal_state_name"],
                                attempt["duration_sec"],
                                (
                                    "{0:.3f}".format(
                                        attempt["final_position_error_m"]
                                    )
                                    if attempt["final_position_error_m"] is not None
                                    else "n/a"
                                ),
                                (
                                    "{0:.2f}".format(attempt["final_yaw_error_deg"])
                                    if attempt["final_yaw_error_deg"] is not None
                                    else "n/a"
                                ),
                                attempt["status_text"] or "",
                            )
                        )
                    lines.append("")

        try:
            with open(self.summary_path, "w") as handle:
                handle.write("\n".join(lines) + "\n")
            rospy.loginfo("Patrol summary written to %s", self.summary_path)
        except (IOError, OSError) as exc:
            rospy.logerr("Failed to write patrol summary %s: %s", self.summary_path, exc)

        if not self.write_yaml_summary:
            return

        yaml_summary = {
            "session_id": self.session_id,
            "session_label": self.session_label,
            "mission_status": self.mission_status,
            "task_file": self.task_file,
            "task_set_id": self.task_set_id,
            "task_set_name": self.task_set_name,
            "map_id": self.map_id,
            "frame_id": self.frame_id,
            "execution_mode": self.execution_mode,
            "enable_two_stage_goal": self.enable_two_stage_goal,
            "enable_progress_monitor": self.enable_progress_monitor,
            "enable_thesis_acceptance": self.enable_thesis_acceptance,
            "retry_limit": self.retry_limit,
            "goal_timeout": self.goal_timeout,
            "progress_timeout": self.progress_timeout,
            "skip_on_failure": self.skip_on_failure,
            "started_at": self.session_started_at.isoformat(),
            "finished_at": (
                self.session_finished_at.isoformat()
                if self.session_finished_at
                else ""
            ),
            "abort_reason": self.abort_reason,
            "metrics": dict(self.metrics),
            "waypoints": self.session_records,
        }

        try:
            with open(self.summary_yaml_path, "w") as handle:
                yaml.safe_dump(
                    yaml_summary,
                    handle,
                    default_flow_style=False,
                    allow_unicode=True,
                )
            rospy.loginfo("Patrol YAML summary written to %s", self.summary_yaml_path)
        except (IOError, OSError) as exc:
            rospy.logerr(
                "Failed to write patrol YAML summary %s: %s",
                self.summary_yaml_path,
                exc,
            )

    def run(self):
        self._ensure_result_dir()
        self.log_configuration()
        self.mission_status = "STARTING"

        try:
            if not self.load_task():
                self.state = "FINISH"
                self.mission_status = "LOAD_TASK_FAILED"
                self.abort_reason = "load_task_failed"
                rospy.logerr("Task manager stopped during LOAD_TASK.")
                return

            if not self.wait_until_ready():
                self.state = "FINISH"
                self.mission_status = "WAIT_READY_FAILED"
                self.abort_reason = "wait_ready_failed"
                rospy.logerr("Task manager stopped during WAIT_READY.")
                return

            self.mission_status = "RUNNING"

            while not rospy.is_shutdown():
                target = self.select_target()
                if target is None:
                    break

                success, waypoint_record = self.execute_target(target)
                self.session_records.append(waypoint_record)

                if success:
                    self.metrics["waypoint_completed"] += 1
                    continue

                self.metrics["waypoint_failed"] += 1
                self.metrics["recovery_trigger_count"] += 1

                if self.skip_on_failure:
                    waypoint_record["final_status"] = "skipped_after_failure"
                    self.metrics["waypoint_skipped"] += 1
                    rospy.logwarn(
                        "Skipping failed waypoint seq=%d id=%s after %d attempts",
                        target["sequence"],
                        target["point_id"],
                        waypoint_record["attempts_used"],
                    )
                    continue

                waypoint_record["final_status"] = "failed_after_retries"
                self.abort_reason = (
                    "waypoint_{0}_failed_after_{1}_attempts".format(
                        target["point_id"], waypoint_record["attempts_used"]
                    )
                )
                self.mission_status = "FAILED"
                rospy.logerr(
                    "Stopping patrol because waypoint seq=%d id=%s failed and "
                    "skip_on_failure=false",
                    target["sequence"],
                    target["point_id"],
                )
                return

            self.mission_status = self._mission_status_after_loop()
        except Exception as exc:
            self.mission_status = "CRASHED"
            self.abort_reason = str(exc)
            rospy.logerr("Unhandled exception in task manager: %s", exc)
            rospy.logerr("%s", traceback.format_exc())
        finally:
            self.state = "FINISH"
            self.session_finished_at = datetime.datetime.now()
            self.write_summary()


def main():
    rospy.init_node("task_manager_node")
    manager = TaskManager()
    manager.run()


if __name__ == "__main__":
    main()
