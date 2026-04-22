#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THESIS_WS="$(cd "${SCRIPT_DIR}/.." && pwd)"
TASK3_SCRIPT="${THESIS_TASK3_SCRIPT:-${THESIS_WS}/scripts/run_task3_active_map.sh}"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <baseline|enhanced> [task_file] [session_label] [extra launch args...]" >&2
  exit 1
fi

mode="$1"
shift

if [[ "${mode}" != "baseline" && "${mode}" != "enhanced" ]]; then
  echo "mode must be baseline or enhanced" >&2
  exit 1
fi

task_file="${1:-${THESIS_WS}/tasks/waypoint_sets/patrol_smoke_v01.yaml}"
if [[ $# -gt 0 ]]; then
  shift
fi

session_label="${1:-line2_${mode}}"
if [[ $# -gt 0 ]]; then
  shift
fi

if [[ ! -x "${TASK3_SCRIPT}" ]]; then
  echo "Task3 launcher not executable: ${TASK3_SCRIPT}" >&2
  exit 1
fi

if [[ ! -f "${task_file}" ]]; then
  echo "Task file not found: ${task_file}" >&2
  exit 1
fi

manager_param_file="${THESIS_WS}/config/tasks/patrol_manager_line2_baseline.yaml"
if [[ "${mode}" == "enhanced" ]]; then
  manager_param_file="${THESIS_WS}/config/tasks/patrol_manager_line2_enhanced.yaml"
fi

echo "Launching line2 execution experiment: mode=${mode}"
echo "Using task file: ${task_file}"
echo "Using session label: ${session_label}"
echo "Using manager params: ${manager_param_file}"

exec "${TASK3_SCRIPT}" \
  task_file:="${task_file}" \
  session_label:="${session_label}" \
  manager_param_file:="${manager_param_file}" \
  "$@"
