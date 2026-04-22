#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import math
from collections import deque

import rospy
from sensor_msgs.msg import LaserScan


def _is_finite(value):
    return not (math.isnan(value) or math.isinf(value))


def _median(values):
    ordered = sorted(values)
    count = len(ordered)
    if count == 0:
        return None

    middle = count // 2
    if count % 2 == 1:
        return ordered[middle]

    return (ordered[middle - 1] + ordered[middle]) / 2.0


class ScanEnhancerNode(object):
    """Minimal thesis-owned scan enhancement frontend."""

    def __init__(self):
        self.input_scan_topic = rospy.get_param("~input_scan_topic", "/scan")
        self.output_scan_topic = rospy.get_param("~output_scan_topic", "/scan_thesis")

        self.min_valid_range = float(rospy.get_param("~min_valid_range", 0.10))
        self.max_valid_range = float(rospy.get_param("~max_valid_range", 12.0))

        self.enable_sector_mask = bool(rospy.get_param("~enable_sector_mask", False))
        self.masked_angle_ranges_deg = list(
            rospy.get_param("~masked_angle_ranges_deg", [])
        )

        self.enable_jump_filter = bool(rospy.get_param("~enable_jump_filter", True))
        self.jump_threshold = float(rospy.get_param("~jump_threshold", 0.35))
        self.neighbor_consistency_threshold = float(
            rospy.get_param("~neighbor_consistency_threshold", 0.12)
        )

        self.enable_temporal_median = bool(
            rospy.get_param("~enable_temporal_median", True)
        )
        self.history_size = max(1, int(rospy.get_param("~history_size", 3)))
        self.min_temporal_samples = max(
            1, int(rospy.get_param("~min_temporal_samples", 2))
        )
        self.history = deque(maxlen=self.history_size)

        self.log_every_n_scans = max(1, int(rospy.get_param("~log_every_n_scans", 30)))
        self.scan_count = 0

        self.publisher = rospy.Publisher(
            self.output_scan_topic, LaserScan, queue_size=10
        )
        self.subscriber = rospy.Subscriber(
            self.input_scan_topic, LaserScan, self._scan_callback, queue_size=10
        )

        rospy.loginfo("thesis scan enhancer started")
        rospy.loginfo("  input_scan_topic: %s", self.input_scan_topic)
        rospy.loginfo("  output_scan_topic: %s", self.output_scan_topic)
        rospy.loginfo(
            "  filters: sector_mask=%s jump_filter=%s temporal_median=%s",
            self.enable_sector_mask,
            self.enable_jump_filter,
            self.enable_temporal_median,
        )

    def _scan_callback(self, msg):
        sanitized = self._sanitize_ranges(msg)
        masked = self._apply_sector_mask(msg, sanitized)
        jump_filtered = self._apply_jump_filter(masked)
        enhanced = self._apply_temporal_median(jump_filtered)

        output = LaserScan()
        output.header = msg.header
        output.angle_min = msg.angle_min
        output.angle_max = msg.angle_max
        output.angle_increment = msg.angle_increment
        output.time_increment = msg.time_increment
        output.scan_time = msg.scan_time
        output.range_min = msg.range_min
        output.range_max = msg.range_max
        output.ranges = enhanced
        output.intensities = list(msg.intensities)

        self.publisher.publish(output)
        self._log_scan_stats(msg.ranges, enhanced)

    def _sanitize_ranges(self, msg):
        lower = max(float(msg.range_min), self.min_valid_range)
        upper = float(msg.range_max)
        if self.max_valid_range > 0.0:
            upper = min(upper, self.max_valid_range)

        sanitized = []
        for value in msg.ranges:
            if not _is_finite(value):
                sanitized.append(float("inf"))
                continue

            if value < lower or value > upper:
                sanitized.append(float("inf"))
                continue

            sanitized.append(float(value))

        return sanitized

    def _apply_sector_mask(self, msg, ranges):
        if not self.enable_sector_mask or not self.masked_angle_ranges_deg:
            return list(ranges)

        output = list(ranges)
        raw_values = list(self.masked_angle_ranges_deg)
        if len(raw_values) % 2 != 0:
            rospy.logwarn_throttle(
                5.0,
                "masked_angle_ranges_deg should contain start/end pairs. "
                "The last value will be ignored.",
            )
            raw_values = raw_values[:-1]

        pairs = []
        for index in range(0, len(raw_values), 2):
            start_deg = float(raw_values[index])
            end_deg = float(raw_values[index + 1])
            pairs.append(
                (
                    math.radians(min(start_deg, end_deg)),
                    math.radians(max(start_deg, end_deg)),
                )
            )

        angle = msg.angle_min
        for i in range(len(output)):
            for start_rad, end_rad in pairs:
                if start_rad <= angle <= end_rad:
                    output[i] = float("inf")
                    break
            angle += msg.angle_increment

        return output

    def _apply_jump_filter(self, ranges):
        if not self.enable_jump_filter or len(ranges) < 3:
            return list(ranges)

        output = list(ranges)
        for i in range(1, len(ranges) - 1):
            prev_value = ranges[i - 1]
            curr_value = ranges[i]
            next_value = ranges[i + 1]

            if not (
                _is_finite(prev_value)
                and _is_finite(curr_value)
                and _is_finite(next_value)
            ):
                continue

            if (
                abs(curr_value - prev_value) > self.jump_threshold
                and abs(curr_value - next_value) > self.jump_threshold
                and abs(prev_value - next_value) < self.neighbor_consistency_threshold
            ):
                output[i] = float("inf")

        return output

    def _apply_temporal_median(self, ranges):
        if not self.enable_temporal_median:
            self.history.append(list(ranges))
            return list(ranges)

        previous_frames = list(self.history)
        output = []

        for i, current_value in enumerate(ranges):
            candidates = []

            if _is_finite(current_value):
                candidates.append(current_value)

            for frame in previous_frames:
                value = frame[i]
                if _is_finite(value):
                    candidates.append(value)

            if len(candidates) >= self.min_temporal_samples:
                output.append(_median(candidates))
            else:
                output.append(current_value)

        self.history.append(list(ranges))
        return output

    def _log_scan_stats(self, raw_ranges, enhanced_ranges):
        self.scan_count += 1
        if self.scan_count % self.log_every_n_scans != 0:
            return

        raw_valid = sum(1 for value in raw_ranges if _is_finite(value))
        enhanced_valid = sum(1 for value in enhanced_ranges if _is_finite(value))
        rospy.loginfo(
            "scan_enhancer stats: raw_valid=%d enhanced_valid=%d total=%d",
            raw_valid,
            enhanced_valid,
            len(enhanced_ranges),
        )


if __name__ == "__main__":
    rospy.init_node("thesis_scan_enhancer")
    ScanEnhancerNode()
    rospy.spin()
