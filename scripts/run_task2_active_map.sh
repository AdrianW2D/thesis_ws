#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THESIS_WS="$(cd "${SCRIPT_DIR}/.." && pwd)"
MAP_REFS="${THESIS_MAP_REFS:-${THESIS_WS}/config/maps/map_refs.yaml}"
TASK2_LAUNCH="${THESIS_TASK2_LAUNCH:-${THESIS_WS}/launch/scenarios/task2_single_goal_nav.launch}"
CATKIN_WS="${THESIS_CATKIN_WS:-${HOME}/catkin_ws}"

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

resolve_map_path() {
  local raw_path="${1:-}"

  if [[ -z "${raw_path}" ]]; then
    return 1
  fi

  case "${raw_path}" in
    \$HOME/*)
      printf '%s\n' "${HOME}${raw_path#\$HOME}"
      ;;
    ~/*)
      printf '%s\n' "${HOME}/${raw_path#~/}"
      ;;
    /*)
      printf '%s\n' "${raw_path}"
      ;;
    thesis_ws/*)
      printf '%s\n' "${THESIS_WS}/${raw_path#thesis_ws/}"
      ;;
    catkin_ws/*)
      printf '%s\n' "${CATKIN_WS}/${raw_path#catkin_ws/}"
      ;;
    maps/*|config/*|launch/*|results/*|bags/*|logs/*|scripts/*)
      printf '%s\n' "${THESIS_WS}/${raw_path}"
      ;;
    *)
      printf '%s\n' "${raw_path}"
      ;;
  esac
}

runtime_map_path="$(extract_map_field runtime_map_path)"
repo_relative_path="$(extract_map_field path_repo_relative)"
default_map_path="${THESIS_WS}/maps/generated/${active_map_id}.yaml"

map_candidates=()
map_candidate_sources=()

if [[ -n "${runtime_map_path}" ]]; then
  map_candidates+=("$(resolve_map_path "${runtime_map_path}")")
  map_candidate_sources+=("runtime_map_path")
fi

if [[ -n "${repo_relative_path}" ]]; then
  map_candidates+=("$(resolve_map_path "${repo_relative_path}")")
  map_candidate_sources+=("path_repo_relative")
fi

map_candidates+=("${default_map_path}")
map_candidate_sources+=("default_thesis_map")

map_file=""
map_source=""
for i in "${!map_candidates[@]}"; do
  candidate="${map_candidates[$i]}"
  if [[ -n "${candidate}" && -f "${candidate}" ]]; then
    map_file="${candidate}"
    map_source="${map_candidate_sources[$i]}"
    break
  fi
done

if [[ -z "${map_file}" ]]; then
  echo "Could not resolve runtime map path for ${active_map_id} from ${MAP_REFS}" >&2
  echo "Checked candidates:" >&2
  for candidate in "${map_candidates[@]}"; do
    [[ -n "${candidate}" ]] && echo "  - ${candidate}" >&2
  done
  exit 1
fi

echo "Launching Task2 with active_map_id=${active_map_id}"
echo "Resolved map source: ${map_source}"
echo "Using map file: ${map_file}"

exec roslaunch "${TASK2_LAUNCH}" map_id:="${active_map_id}" map_file:="${map_file}" "$@"
