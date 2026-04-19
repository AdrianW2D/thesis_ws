#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THESIS_WS="$(cd "${SCRIPT_DIR}/.." && pwd)"
MAP_REFS="${THESIS_WS}/config/maps/map_refs.yaml"
TASK2_LAUNCH="${THESIS_WS}/launch/scenarios/task2_single_goal_nav.launch"

if ! command -v roslaunch >/dev/null 2>&1; then
  echo "roslaunch not found. Source /opt/ros/melodic and the catkin workspaces first." >&2
  exit 1
fi

if [[ ! -f "${MAP_REFS}" ]]; then
  echo "Map index not found: ${MAP_REFS}" >&2
  exit 1
fi

active_map_id="$(
  awk -F': ' '/^active_map_id:/ {
    gsub(/"/, "", $2);
    print $2;
    exit
  }' "${MAP_REFS}"
)"

if [[ -z "${active_map_id}" ]]; then
  echo "active_map_id is empty in ${MAP_REFS}" >&2
  exit 1
fi

extract_map_field() {
  local field_name="$1"
  awk -v target="${active_map_id}" -v field_name="${field_name}" '
    $0 ~ "^  " target ":" {in_target=1; next}
    in_target && $0 ~ "^  [^ ]" {in_target=0}
    in_target && $0 ~ "^    " field_name ":" {
      sub(/^[^:]*:[[:space:]]*/, "");
      gsub(/"/, "");
      print;
      exit
    }
  ' "${MAP_REFS}"
}

map_file="$(extract_map_field runtime_map_path)"

if [[ -z "${map_file}" ]]; then
  repo_relative_path="$(extract_map_field path_repo_relative)"
  case "${repo_relative_path}" in
    thesis_ws/*)
      map_file="${HOME}/${repo_relative_path}"
      ;;
    catkin_ws/*)
      map_file="${HOME}/${repo_relative_path}"
      ;;
  esac
fi

map_file="${map_file/\$HOME/${HOME}}"

if [[ -z "${map_file}" ]]; then
  echo "Could not resolve runtime map path for ${active_map_id} from ${MAP_REFS}" >&2
  exit 1
fi

if [[ ! -f "${map_file}" ]]; then
  echo "Resolved map file does not exist: ${map_file}" >&2
  exit 1
fi

echo "Launching Task2 with active_map_id=${active_map_id}"
echo "Using map file: ${map_file}"

exec roslaunch "${TASK2_LAUNCH}" map_id:="${active_map_id}" map_file:="${map_file}" "$@"
