#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import os
import time
import traceback

import actionlib
import yaml

import rospy
from geometry_msgs.msg import PoseWithCovarianceStamped
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from tf.transformations import quaternion_from_euler


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


class TaskManager(object):
    """A1 task manager for minimal thesis patrol execution."""

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
        self.retry_limit = int(rospy.get_param("~retry_limit", 2))
        self.goal_timeout = float(rospy.get_param("~goal_timeout", 60.0))
        self.skip_on_failure = bool(rospy.get_param("~skip_on_failure", True))
        self.ready_timeout = float(rospy.get_param("~ready_timeout", 30.0))

        self.session_started_at = datetime.datetime.now()
        self.session_id = "patrol_{0}".format(
            self.session_started_at.strftime("%Y%m%d_%H%M%S")
        )
        self.summary_path = os.path.join(self.result_dir, self.session_id + ".md")

        self.task_set_id = ""
        self.task_set_name = ""
        self.map_id = ""
        self.frame_id = "map"
        self.raw_task = None
        self.task_points = []
        self.current_index = -1
        self.current_goal = None
        self.latest_result = None
        self.latest_amcl_pose_msg = None
        self.session_records = []
        self.mission_status = "INIT"
        self.abort_reason = ""
        self.session_finished_at = None
        self.goal_active = False

        self.move_base_client = actionlib.SimpleActionClient(
            "move_base", MoveBaseAction
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

    def log_configuration(self):
        rospy.loginfo("Task manager session: %s", self.session_id)
        rospy.loginfo("  task_file: %s", self.task_file)
        rospy.loginfo("  result_dir: %s", self.result_dir)
        rospy.loginfo("  retry_limit: %d", self.retry_limit)
        rospy.loginfo("  goal_timeout: %.1f", self.goal_timeout)
        rospy.loginfo("  skip_on_failure: %s", self.skip_on_failure)
        rospy.loginfo("  ready_timeout: %.1f", self.ready_timeout)
        rospy.loginfo("  summary_path: %s", self.summary_path)

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

    def _goal_state_name(self, goal_state):
        return GOAL_STATUS_NAMES.get(goal_state, "UNKNOWN_{0}".format(goal_state))

    def _build_move_base_goal(self, target):
        quaternion = quaternion_from_euler(0.0, 0.0, target["pose"]["yaw"])
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = self.frame_id
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose.position.x = target["pose"]["x"]
        goal.target_pose.pose.position.y = target["pose"]["y"]
        goal.target_pose.pose.position.z = 0.0
        goal.target_pose.pose.orientation.x = quaternion[0]
        goal.target_pose.pose.orientation.y = quaternion[1]
        goal.target_pose.pose.orientation.z = quaternion[2]
        goal.target_pose.pose.orientation.w = quaternion[3]
        return goal

    def _parse_point(self, raw_point, default_sequence, raw_index):
        context_name = "point[{0}]".format(raw_index)
        point = self._require_mapping(raw_point, context_name)

        enabled = bool(point.get("enabled", False))
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
        """Load task YAML and parse enabled waypoints for A1."""
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
            rospy.logwarn("Task file map_id is empty. A1 only records it and does not block.")

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
        """
        Wait for navigation readiness.

        A1 frozen rule:
        - /move_base action server must be available
        - at least one /amcl_pose message must be received
        """
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
            rospy.logerr(
                "Ready timeout exhausted before waiting for /amcl_pose"
            )
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

        pose = self.latest_amcl_pose_msg.pose.pose.position
        rospy.loginfo(
            "Ready gate passed. First /amcl_pose received at (%.3f, %.3f)",
            pose.x,
            pose.y,
        )
        return True

    def select_target(self):
        """Pick the next waypoint from the loaded task."""
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

    def send_goal(self, target):
        """Send a MoveBase goal for the selected waypoint."""
        self.state = "SEND_GOAL"
        goal = self._build_move_base_goal(target)
        self.move_base_client.send_goal(goal)
        self.goal_active = True

        rospy.loginfo(
            "Sent move_base goal: seq=%d id=%s frame=%s pose=(%.3f, %.3f, %.3f)",
            target["sequence"],
            target["point_id"],
            self.frame_id,
            target["pose"]["x"],
            target["pose"]["y"],
            target["pose"]["yaw"],
        )
        return {
            "sent_at": time.time(),
            "goal_frame_id": self.frame_id,
        }

    def wait_for_goal_result(self):
        """Wait for the current move_base goal result with timeout handling."""
        self.state = "WAIT_RESULT"
        rospy.loginfo(
            "Waiting for move_base result (timeout: %.1fs)", self.goal_timeout
        )

        finished = self.move_base_client.wait_for_result(
            rospy.Duration.from_sec(self.goal_timeout)
        )

        if not finished:
            rospy.logwarn(
                "move_base result timed out after %.1fs. Canceling goal first.",
                self.goal_timeout,
            )
            self.move_base_client.cancel_goal()
            self.goal_active = False
            rospy.sleep(0.2)
            goal_state = self.move_base_client.get_state()
            return {
                "timed_out": True,
                "goal_state": goal_state,
                "goal_state_name": self._goal_state_name(goal_state),
                "status_text": self.move_base_client.get_goal_status_text(),
                "finished_at": time.time(),
            }

        self.goal_active = False
        goal_state = self.move_base_client.get_state()
        return {
            "timed_out": False,
            "goal_state": goal_state,
            "goal_state_name": self._goal_state_name(goal_state),
            "status_text": self.move_base_client.get_goal_status_text(),
            "finished_at": time.time(),
        }

    def handle_result(self, target, attempt_index, dispatch_result, wait_result):
        """Handle move_base success / fail / timeout."""
        self.state = "HANDLE_RESULT"
        duration_sec = max(0.0, wait_result["finished_at"] - dispatch_result["sent_at"])

        if wait_result["timed_out"]:
            attempt_status = "timeout"
            success = False
        elif wait_result["goal_state"] == 3:
            attempt_status = "succeeded"
            success = True
        else:
            attempt_status = wait_result["goal_state_name"].lower()
            success = False

        attempt_record = {
            "attempt_index": attempt_index,
            "status": attempt_status,
            "success": success,
            "timed_out": wait_result["timed_out"],
            "goal_state": wait_result["goal_state"],
            "goal_state_name": wait_result["goal_state_name"],
            "status_text": wait_result["status_text"],
            "duration_sec": duration_sec,
            "goal_frame_id": dispatch_result["goal_frame_id"],
        }

        rospy.loginfo(
            "Waypoint attempt finished: seq=%d id=%s attempt=%d status=%s "
            "goal_state=%s duration=%.2fs",
            target["sequence"],
            target["point_id"],
            attempt_index,
            attempt_record["status"],
            attempt_record["goal_state_name"],
            attempt_record["duration_sec"],
        )
        return success, attempt_record

    def execute_target(self, target):
        max_attempts = self.retry_limit + 1
        waypoint_record = {
            "sequence": target["sequence"],
            "point_id": target["point_id"],
            "point_name": target["point_name"],
            "task_type": target["task_type"],
            "pose": target["pose"],
            "attempts": [],
            "attempts_used": 0,
            "final_status": "not_started",
            "final_goal_state_name": "",
            "final_status_text": "",
        }

        for attempt_index in range(1, max_attempts + 1):
            dispatch_result = self.send_goal(target)
            wait_result = self.wait_for_goal_result()
            success, attempt_record = self.handle_result(
                target, attempt_index, dispatch_result, wait_result
            )

            waypoint_record["attempts"].append(attempt_record)
            waypoint_record["attempts_used"] = attempt_index
            waypoint_record["final_status"] = attempt_record["status"]
            waypoint_record["final_goal_state_name"] = attempt_record["goal_state_name"]
            waypoint_record["final_status_text"] = attempt_record["status_text"]

            if success:
                return True, waypoint_record

            if attempt_index < max_attempts:
                rospy.logwarn(
                    "Retrying waypoint seq=%d id=%s (%d/%d)",
                    target["sequence"],
                    target["point_id"],
                    attempt_index + 1,
                    max_attempts,
                )

        if self.skip_on_failure:
            waypoint_record["final_status"] = "skipped_after_failure"
        else:
            waypoint_record["final_status"] = "failed_after_retries"
        return False, waypoint_record

    def write_summary(self):
        """Write patrol session summary to results/patrol."""
        completed_count = 0
        skipped_count = 0
        failed_count = 0
        for record in self.session_records:
            if record["final_status"] == "succeeded":
                completed_count += 1
            elif record["final_status"] == "skipped_after_failure":
                skipped_count += 1
            else:
                failed_count += 1

        lines = [
            "# Patrol Session Summary",
            "",
            "- session_id: {0}".format(self.session_id),
            "- mission_status: {0}".format(self.mission_status),
            "- task_file: {0}".format(self.task_file),
            "- task_set_id: {0}".format(self.task_set_id or ""),
            "- task_set_name: {0}".format(self.task_set_name or ""),
            "- map_id: {0}".format(self.map_id or ""),
            "- frame_id: {0}".format(self.frame_id or ""),
            "- started_at: {0}".format(self.session_started_at.isoformat()),
            "- finished_at: {0}".format(
                self.session_finished_at.isoformat()
                if self.session_finished_at
                else ""
            ),
            "- retry_limit: {0}".format(self.retry_limit),
            "- goal_timeout: {0}".format(self.goal_timeout),
            "- skip_on_failure: {0}".format(self.skip_on_failure),
            "- waypoint_total: {0}".format(len(self.task_points)),
            "- waypoint_completed: {0}".format(completed_count),
            "- waypoint_skipped: {0}".format(skipped_count),
            "- waypoint_failed: {0}".format(failed_count),
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
                        "- pose: ({0:.3f}, {1:.3f}, {2:.3f})".format(
                            record["pose"]["x"],
                            record["pose"]["y"],
                            record["pose"]["yaw"],
                        ),
                        "",
                        "Attempts:",
                    ]
                )
                for attempt in record["attempts"]:
                    lines.append(
                        "- attempt {0}: status={1}, goal_state={2}, duration={3:.2f}s, text={4}".format(
                            attempt["attempt_index"],
                            attempt["status"],
                            attempt["goal_state_name"],
                            attempt["duration_sec"],
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
                    continue

                if self.skip_on_failure:
                    rospy.logwarn(
                        "Skipping failed waypoint seq=%d id=%s after %d attempts",
                        target["sequence"],
                        target["point_id"],
                        waypoint_record["attempts_used"],
                    )
                    continue

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

            if rospy.is_shutdown():
                self.mission_status = "INTERRUPTED"
            elif any(
                record["final_status"] == "skipped_after_failure"
                for record in self.session_records
            ):
                self.mission_status = "COMPLETED_WITH_SKIPS"
            else:
                self.mission_status = "COMPLETED"
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
