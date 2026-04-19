#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Resolve the deployed thesis_ws root from the script location instead of
# relying on any local repository path assumption.
THESIS_WS="$(cd "${SCRIPT_DIR}/.." && pwd)"
MAP_DIR="${THESIS_WS}/maps/generated"
RESULT_DIR="${THESIS_WS}/results/mapping"

if ! command -v rosrun >/dev/null 2>&1; then
  echo "rosrun not found. Source /opt/ros/melodic and the catkin workspaces first." >&2
  exit 1
fi

mkdir -p "${MAP_DIR}" "${RESULT_DIR}"

map_name="${1:-task1_map_$(date +%Y%m%d_%H%M%S)}"
map_prefix="${MAP_DIR}/${map_name}"
result_note="${RESULT_DIR}/${map_name}.md"

echo "Saving map to: ${map_prefix}"
rosrun map_server map_saver -f "${map_prefix}"

cat > "${result_note}" <<EOF
# ${map_name}

- task: Task1 mapping session
- saved_at: $(date '+%Y-%m-%d %H:%M:%S')
- map_yaml: maps/generated/${map_name}.yaml
- map_pgm: maps/generated/${map_name}.pgm
- note: Fill in environment notes, operator remarks, screenshots, and any issues observed during the mapping session.
EOF

echo "Created result note: ${result_note}"
