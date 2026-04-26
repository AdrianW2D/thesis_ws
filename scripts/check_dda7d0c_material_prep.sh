#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THESIS_WS="$(cd "${SCRIPT_DIR}/.." && pwd)"

EXPECTED_VERSION="${THESIS_EXPECTED_VERSION:-dda7d0c}"
EXPECTED_MAP_ID="${THESIS_EXPECTED_MAP_ID:-task1_lab_v02}"
EXPECTED_MAP_FILE="${THESIS_EXPECTED_MAP_FILE:-${THESIS_WS}/maps/generated/${EXPECTED_MAP_ID}.yaml}"
TASK_FILE="${THESIS_MATERIAL_TASK_FILE:-${THESIS_WS}/tasks/waypoint_sets/2026_4.yaml}"
MAP_REFS="${THESIS_MAP_REFS:-${THESIS_WS}/config/maps/map_refs.yaml}"

failures=0
warnings=0

pass() {
  printf '[OK] %s\n' "$1"
}

warn() {
  printf '[WARN] %s\n' "$1"
  warnings=$((warnings + 1))
}

fail() {
  printf '[FAIL] %s\n' "$1"
  failures=$((failures + 1))
}

check_file() {
  local file_path="$1"
  local label="$2"
  if [[ -f "${file_path}" ]]; then
    pass "${label}: ${file_path}"
  else
    fail "${label} missing: ${file_path}"
  fi
}

check_script() {
  local file_path="$1"
  local label="$2"
  if [[ -x "${file_path}" ]]; then
    pass "${label}: ${file_path}"
  elif [[ -f "${file_path}" ]]; then
    warn "${label} exists but is not executable: ${file_path}"
  else
    fail "${label} missing: ${file_path}"
  fi
}

echo "== thesis_ws dda7d0c material collection preflight =="
echo "workspace: ${THESIS_WS}"
echo "expected_version: ${EXPECTED_VERSION}"
echo "expected_map_id: ${EXPECTED_MAP_ID}"
echo "expected_map_file: ${EXPECTED_MAP_FILE}"
echo "task_file: ${TASK_FILE}"
echo

if command -v git >/dev/null 2>&1 && [[ -d "${THESIS_WS}/.git" ]]; then
  current_version="$(git -C "${THESIS_WS}" rev-parse --short HEAD 2>/dev/null || true)"
  if [[ -z "${current_version}" ]]; then
    fail "Could not resolve current git revision from ${THESIS_WS}"
  elif [[ "${current_version}" == "${EXPECTED_VERSION}" ]]; then
    pass "Current version is ${current_version}"
  else
    warn "Current version is ${current_version}; expected ${EXPECTED_VERSION}"
  fi
else
  warn "Git revision check skipped because ${THESIS_WS} is not a git checkout"
fi

if command -v roslaunch >/dev/null 2>&1; then
  pass "roslaunch is available"
else
  warn "roslaunch not found in current shell; source ROS before running experiments"
fi

if command -v catkin_make >/dev/null 2>&1; then
  pass "catkin_make is available"
else
  warn "catkin_make not found in current shell; source ROS before building"
fi

check_file "${MAP_REFS}" "Map index"
check_script "${THESIS_WS}/scripts/run_task2_active_map.sh" "Task2 launcher"
check_script "${THESIS_WS}/scripts/run_task3_active_map.sh" "Task3 patrol launcher"
check_script "${THESIS_WS}/scripts/run_task3_waypoint_capture_active_map.sh" "Task3 capture launcher"
check_script "${THESIS_WS}/scripts/run_task3_execution_experiment.sh" "line2 launcher"
check_script "${THESIS_WS}/scripts/init_line2_execution_record.sh" "line2 record template"
check_script "${THESIS_WS}/scripts/generate_task3_coverage_task.sh" "Coverage generator launcher"

if [[ -f "${EXPECTED_MAP_FILE}" ]]; then
  pass "Expected Task1/Task2/Task3 map exists"
else
  warn "Expected map does not exist yet: ${EXPECTED_MAP_FILE}"
fi

if [[ -f "${TASK_FILE}" ]]; then
  pass "Task3 patrol task file exists"
else
  warn "Task3 patrol task file does not exist yet: ${TASK_FILE}"
  warn "Create it through Task3 waypoint capture before patrol execution"
fi

if [[ -f "${MAP_REFS}" ]]; then
  active_map_id="$(
    awk -F': ' '/^active_map_id:/ {
      gsub(/"/, "", $2);
      print $2;
      exit
    }' "${MAP_REFS}"
  )"

  if [[ -z "${active_map_id}" ]]; then
    fail "active_map_id is empty in ${MAP_REFS}"
  elif [[ "${active_map_id}" == "${EXPECTED_MAP_ID}" ]]; then
    pass "active_map_id matches ${EXPECTED_MAP_ID}"
  else
    warn "active_map_id is ${active_map_id}; expected ${EXPECTED_MAP_ID}"
  fi

  if grep -q "^  ${EXPECTED_MAP_ID}:" "${MAP_REFS}"; then
    pass "Map index contains entry for ${EXPECTED_MAP_ID}"
  else
    warn "Map index does not contain a ${EXPECTED_MAP_ID} entry yet"
  fi

  expected_runtime_path="\$HOME/thesis_ws/maps/generated/${EXPECTED_MAP_ID}.yaml"
  if grep -q "runtime_map_path: \"${expected_runtime_path}\"" "${MAP_REFS}"; then
    pass "runtime_map_path for ${EXPECTED_MAP_ID} matches expected thesis path"
  else
    warn "runtime_map_path for ${EXPECTED_MAP_ID} does not match ${expected_runtime_path}"
  fi
fi

check_file "${THESIS_WS}/config/tasks/patrol_manager_params.yaml" "Task3 default manager config"
check_file "${THESIS_WS}/config/tasks/patrol_manager_line2_baseline.yaml" "line2 baseline config"
check_file "${THESIS_WS}/config/tasks/patrol_manager_line2_enhanced.yaml" "line2 enhanced config"
check_file "${THESIS_WS}/config/tasks/coverage_schema.yaml" "Coverage schema"
check_file "${THESIS_WS}/tasks/waypoint_sets/patrol_smoke_v01.yaml" "Task3 smoke patrol task"
check_file "${THESIS_WS}/tasks/waypoint_sets/single_goal_smoke_v01.yaml" "line2 single-goal smoke task"
check_file "${THESIS_WS}/tasks/coverage_sets/coverage_rect_smoke_v01.yaml" "Coverage smoke config"

for dir_path in \
  "${THESIS_WS}/results/mapping" \
  "${THESIS_WS}/results/navigation" \
  "${THESIS_WS}/results/patrol"; do
  if [[ -d "${dir_path}" ]]; then
    pass "Result directory exists: ${dir_path}"
  else
    fail "Result directory missing: ${dir_path}"
  fi
done

echo
echo "== Suggested next steps =="
if [[ ! -f "${EXPECTED_MAP_FILE}" ]]; then
  echo "1. Build or rebuild the map:"
  echo "   \"\$HOME/thesis_ws/scripts/run_task1_scan_frontend_experiment.sh\" baseline task1_material_baseline"
  echo "   \"\$HOME/thesis_ws/scripts/save_task1_map.sh\" ${EXPECTED_MAP_ID}"
else
  echo "1. Start Task2 on the active map:"
  echo "   \"\$HOME/thesis_ws/scripts/run_task2_active_map.sh\""
fi
echo "2. Capture or verify Task3 waypoints:"
echo "   export THESIS_TASK3_CAPTURE_FILE=\"${TASK_FILE}\""
echo "   \"\$HOME/thesis_ws/scripts/run_task3_waypoint_capture_active_map.sh\""
echo "3. Run Task3 patrol:"
echo "   THESIS_TASK3_TASK_FILE=\"${TASK_FILE}\" \"\$HOME/thesis_ws/scripts/run_task3_active_map.sh\""
echo "4. Run line2 comparison if needed:"
echo "   \"\$HOME/thesis_ws/scripts/init_line2_execution_record.sh\" exp_line2_lab_v02"
echo "5. Generate coverage waypoints if needed:"
echo "   \"\$HOME/thesis_ws/scripts/generate_task3_coverage_task.sh\" \"\$HOME/thesis_ws/tasks/coverage_sets/coverage_rect_smoke_v01.yaml\""

echo
if (( failures > 0 )); then
  echo "Preflight completed with ${failures} failure(s) and ${warnings} warning(s)."
  exit 1
fi

echo "Preflight completed with ${warnings} warning(s) and no hard failures."
