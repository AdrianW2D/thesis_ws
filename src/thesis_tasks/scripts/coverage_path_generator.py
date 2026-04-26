#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import io
import math
import os
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "Coverage generation failed: PyYAML is not available for the selected "
        "Python interpreter.\n"
    )
    sys.exit(1)


VALID_DIRECTIONS = ("x_major", "y_major")
VALID_START_CORNERS = ("lower_left", "lower_right", "upper_left", "upper_right")


def _resolve_path(raw_path, base_dir=None):
    path = os.path.expanduser(os.path.expandvars(str(raw_path)))
    if not os.path.isabs(path) and base_dir:
        path = os.path.join(base_dir, path)
    return os.path.abspath(path)


def _require_mapping(value, field_name):
    if not isinstance(value, dict):
        raise ValueError("Field '{0}' must be a mapping".format(field_name))
    return value


def _require_field(mapping, field_name, context_name):
    if field_name not in mapping:
        raise ValueError(
            "Missing required field '{0}' in {1}".format(field_name, context_name)
        )
    return mapping[field_name]


def _as_float(value, field_name):
    try:
        return float(value)
    except Exception:
        raise ValueError("Field '{0}' must be numeric".format(field_name))


def _build_lane_positions(start_value, end_value, spacing):
    positions = [start_value]
    cursor = start_value
    epsilon = 1e-9

    while cursor + spacing < end_value - epsilon:
        cursor += spacing
        positions.append(cursor)

    if abs(positions[-1] - end_value) > 1e-6:
        positions.append(end_value)

    return positions


def _normalize_rectangle(config):
    area = _require_mapping(_require_field(config, "area", "coverage task"), "area")
    origin = _require_mapping(
        _require_field(area, "origin", "area"), "area.origin"
    )
    sweep = _require_mapping(_require_field(config, "sweep", "coverage task"), "sweep")
    output = _require_mapping(
        _require_field(config, "output", "coverage task"), "output"
    )

    area_type = str(_require_field(area, "type", "area")).strip()
    if area_type != "rectangle":
        raise ValueError(
            "Unsupported area.type '{0}'. Only 'rectangle' is supported.".format(
                area_type
            )
        )

    origin_x = _as_float(_require_field(origin, "x", "area.origin"), "area.origin.x")
    origin_y = _as_float(_require_field(origin, "y", "area.origin"), "area.origin.y")
    width = _as_float(_require_field(area, "width", "area"), "area.width")
    height = _as_float(_require_field(area, "height", "area"), "area.height")

    if width <= 0.0:
        raise ValueError("area.width must be > 0")
    if height <= 0.0:
        raise ValueError("area.height must be > 0")

    direction = str(_require_field(sweep, "direction", "sweep")).strip().lower()
    if direction not in VALID_DIRECTIONS:
        raise ValueError(
            "Unsupported sweep.direction '{0}'. Supported: {1}".format(
                direction, ", ".join(VALID_DIRECTIONS)
            )
        )

    lane_spacing = _as_float(
        _require_field(sweep, "lane_spacing", "sweep"), "sweep.lane_spacing"
    )
    boundary_margin = _as_float(
        _require_field(sweep, "boundary_margin", "sweep"),
        "sweep.boundary_margin",
    )
    start_corner = str(_require_field(sweep, "start_corner", "sweep")).strip().lower()

    if lane_spacing <= 0.0:
        raise ValueError("sweep.lane_spacing must be > 0")
    if boundary_margin < 0.0:
        raise ValueError("sweep.boundary_margin must be >= 0")
    if start_corner not in VALID_START_CORNERS:
        raise ValueError(
            "Unsupported sweep.start_corner '{0}'. Supported: {1}".format(
                start_corner, ", ".join(VALID_START_CORNERS)
            )
        )

    x_min = origin_x + boundary_margin
    y_min = origin_y + boundary_margin
    x_max = origin_x + width - boundary_margin
    y_max = origin_y + height - boundary_margin

    if x_max <= x_min or y_max <= y_min:
        raise ValueError(
            "boundary_margin is too large for the configured rectangle. "
            "Effective area becomes empty."
        )

    return {
        "area_type": area_type,
        "origin_x": origin_x,
        "origin_y": origin_y,
        "width": width,
        "height": height,
        "direction": direction,
        "lane_spacing": lane_spacing,
        "boundary_margin": boundary_margin,
        "start_corner": start_corner,
        "x_min": x_min,
        "x_max": x_max,
        "y_min": y_min,
        "y_max": y_max,
        "output": output,
    }


def _build_lanes(rectangle):
    direction = rectangle["direction"]
    start_corner = rectangle["start_corner"]
    x_min = rectangle["x_min"]
    x_max = rectangle["x_max"]
    y_min = rectangle["y_min"]
    y_max = rectangle["y_max"]
    lane_spacing = rectangle["lane_spacing"]

    lanes = []

    if direction == "x_major":
        forward_positions = _build_lane_positions(y_min, y_max, lane_spacing)
        if start_corner in ("upper_left", "upper_right"):
            forward_positions = list(reversed(forward_positions))
        initial_forward = start_corner in ("lower_left", "upper_left")

        for index, lane_y in enumerate(forward_positions):
            forward = initial_forward if index % 2 == 0 else not initial_forward
            if forward:
                start = {"x": x_min, "y": lane_y}
                end = {"x": x_max, "y": lane_y}
            else:
                start = {"x": x_max, "y": lane_y}
                end = {"x": x_min, "y": lane_y}
            yaw = math.atan2(end["y"] - start["y"], end["x"] - start["x"])
            lanes.append(
                {"start": start, "end": end, "yaw": yaw, "lane_index": index + 1}
            )
    else:
        forward_positions = _build_lane_positions(x_min, x_max, lane_spacing)
        if start_corner in ("lower_right", "upper_right"):
            forward_positions = list(reversed(forward_positions))
        initial_forward = start_corner in ("lower_left", "lower_right")

        for index, lane_x in enumerate(forward_positions):
            forward = initial_forward if index % 2 == 0 else not initial_forward
            if forward:
                start = {"x": lane_x, "y": y_min}
                end = {"x": lane_x, "y": y_max}
            else:
                start = {"x": lane_x, "y": y_max}
                end = {"x": lane_x, "y": y_min}
            yaw = math.atan2(end["y"] - start["y"], end["x"] - start["x"])
            lanes.append(
                {"start": start, "end": end, "yaw": yaw, "lane_index": index + 1}
            )

    if len(lanes) < 2:
        raise ValueError(
            "The configured rectangle produces fewer than 2 effective sweep lanes. "
            "Increase the area size or reduce lane_spacing / boundary_margin."
        )

    return lanes


def _build_waypoint_task(config, rectangle, lanes, config_path, output_path):
    output = rectangle["output"]
    default_task_type = str(output.get("default_task_type", "inspect")).strip()
    default_stay_time_sec = float(output.get("default_stay_time_sec", 1.0))
    tolerance_xy = float(output.get("tolerance_xy", 0.30))
    tolerance_yaw_deg = float(output.get("tolerance_yaw_deg", 20.0))
    output_tag = str(output.get("tag", "coverage")).strip() or "coverage"
    output_note = str(output.get("note", "")).strip()

    points = []
    sequence = 1

    for lane in lanes:
        lane_label = "lane{0:02d}".format(lane["lane_index"])
        for point_role, pose in (("entry", lane["start"]), ("exit", lane["end"])):
            point_id = "P{0:02d}".format(sequence)
            point_name = "{0}_{1}".format(lane_label, point_role)
            note_parts = [
                "Generated from {0}".format(os.path.basename(config_path)),
                "role={0}".format(point_role),
            ]
            if output_note:
                note_parts.append(output_note)

            points.append(
                {
                    "point_id": point_id,
                    "point_name": point_name,
                    "sequence": sequence,
                    "pose": {
                        "x": round(pose["x"], 3),
                        "y": round(pose["y"], 3),
                        "yaw": round(lane["yaw"], 6),
                    },
                    "tolerance": {
                        "xy": round(tolerance_xy, 3),
                        "yaw_deg": round(tolerance_yaw_deg, 2),
                    },
                    "task_type": default_task_type,
                    "stay_time_sec": round(default_stay_time_sec, 2),
                    "expected_action": "coverage_pass",
                    "enabled": True,
                    "tags": [output_tag, "coverage", lane_label, point_role],
                    "note": "; ".join(note_parts),
                }
            )
            sequence += 1

    task_id = str(_require_field(config, "coverage_task_id", "coverage task")).strip()
    task_name = str(
        _require_field(config, "coverage_task_name", "coverage task")
    ).strip()
    map_id = str(_require_field(config, "map_id", "coverage task")).strip()
    frame_id = str(_require_field(config, "frame_id", "coverage task")).strip() or "map"
    description = str(config.get("description", "")).strip()

    return {
        "task_set_id": task_id,
        "task_set_name": task_name,
        "map_id": map_id,
        "frame_id": frame_id,
        "description": description or "Generated bow coverage waypoint task.",
        "generated_by": "thesis_tasks/coverage_path_generator.py",
        "coverage_source_file": config_path,
        "coverage_output_file": output_path,
        "coverage_metadata": {
            "area_type": rectangle["area_type"],
            "origin": {
                "x": round(rectangle["origin_x"], 3),
                "y": round(rectangle["origin_y"], 3),
            },
            "width": round(rectangle["width"], 3),
            "height": round(rectangle["height"], 3),
            "effective_bounds": {
                "x_min": round(rectangle["x_min"], 3),
                "x_max": round(rectangle["x_max"], 3),
                "y_min": round(rectangle["y_min"], 3),
                "y_max": round(rectangle["y_max"], 3),
            },
            "sweep_direction": rectangle["direction"],
            "lane_spacing": round(rectangle["lane_spacing"], 3),
            "boundary_margin": round(rectangle["boundary_margin"], 3),
            "start_corner": rectangle["start_corner"],
            "lane_count": len(lanes),
            "waypoint_count": len(points),
        },
        "points": points,
    }


def _load_yaml(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("Coverage config root must be a mapping")
    return data


def _write_yaml(path, data):
    parent_dir = os.path.dirname(path)
    if parent_dir and not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)

    with io.open(path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, default_flow_style=False, allow_unicode=False)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a bow coverage waypoint YAML for Task3."
    )
    parser.add_argument("--config", required=True, help="Coverage config YAML path")
    parser.add_argument(
        "--output",
        help="Optional override for the generated waypoint YAML path",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing output file",
    )
    args = parser.parse_args()

    config_path = _resolve_path(args.config, os.getcwd())
    config_dir = os.path.dirname(config_path)
    config = _load_yaml(config_path)
    rectangle = _normalize_rectangle(config)

    output_path = args.output or rectangle["output"].get("task_file")
    if not output_path:
        raise ValueError("output.task_file is required when --output is not provided")
    output_path = _resolve_path(output_path, config_dir)

    if os.path.exists(output_path) and not args.overwrite:
        raise ValueError(
            "Output file already exists: {0}. Use --overwrite to replace it.".format(
                output_path
            )
        )

    lanes = _build_lanes(rectangle)
    task_data = _build_waypoint_task(config, rectangle, lanes, config_path, output_path)
    _write_yaml(output_path, task_data)

    print("Coverage config: {0}".format(config_path))
    print("Generated task file: {0}".format(output_path))
    print(
        "Sweep summary: direction={0}, lanes={1}, waypoints={2}".format(
            rectangle["direction"], len(lanes), len(task_data["points"])
        )
    )
    print(
        "Effective bounds: x[{0:.3f}, {1:.3f}] y[{2:.3f}, {3:.3f}]".format(
            rectangle["x_min"],
            rectangle["x_max"],
            rectangle["y_min"],
            rectangle["y_max"],
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Coverage generation failed: {0}".format(exc), file=sys.stderr)
        sys.exit(1)
