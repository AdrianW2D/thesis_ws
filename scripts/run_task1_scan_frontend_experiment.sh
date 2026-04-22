#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THESIS_WS="$(cd "${SCRIPT_DIR}/.." && pwd)"
TASK1_LAUNCH="${THESIS_TASK1_LAUNCH:-${THESIS_WS}/launch/scenarios/task1_mapping_session.launch}"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <baseline|enhanced> [session_name] [extra roslaunch args...]" >&2
  exit 1
fi

mode="$1"
shift

if [[ "${mode}" != "baseline" && "${mode}" != "enhanced" ]]; then
  echo "mode must be baseline or enhanced" >&2
  exit 1
fi

session_name="${1:-line1_task1_${mode}_$(date +%Y%m%d_%H%M%S)}"
if [[ $# -gt 0 ]]; then
  shift
fi

if ! command -v roslaunch >/dev/null 2>&1; then
  echo "roslaunch not found. Source /opt/ros/melodic and the catkin workspaces first." >&2
  exit 1
fi

use_scan_enhancer="false"
mapping_scan_topic="/scan"
scan_param_file="${THESIS_WS}/config/overlays/sensing/scan_enhancer_baseline.yaml"

if [[ "${mode}" == "enhanced" ]]; then
  use_scan_enhancer="true"
  mapping_scan_topic="/scan_thesis"
  scan_param_file="${THESIS_WS}/config/overlays/sensing/scan_enhancer_enhanced.yaml"
fi

result_note="${THESIS_WS}/results/mapping/${session_name}.md"
mkdir -p "$(dirname "${result_note}")"

cat > "${result_note}" <<EOF
# ${session_name}

- experiment_line: line1_scan_frontend
- task: task1_mapping
- variant: ${mode}
- session_name: ${session_name}
- scan_input_topic: /scan
- scan_output_topic: ${mapping_scan_topic}
- scan_enhancer_enabled: ${use_scan_enhancer}
- scan_enhancer_param_file: ${scan_param_file#${THESIS_WS}/}
- bag_path: bags/mapping/${session_name}.bag

## Metrics

| item | value | note |
| --- | --- | --- |
| map_name |  | e.g. task1_lab_line1_${mode}_v01 |
| mapping_duration_sec |  |  |
| map_usable_for_task2 |  | yes/no |
| wall_continuity_score_1_5 |  | manual score |
| ghosting_score_1_5 |  | lower is better |
| corner_closure_score_1_5 |  | manual score |
| operator_note |  |  |

## Screenshot checklist

- [ ] RViz screenshot saved
- [ ] saved map yaml/pgm recorded
- [ ] anomalies noted
EOF

echo "Launching Task1 scan-frontend experiment: mode=${mode} session=${session_name}"
echo "Initialized result note: ${result_note}"

exec roslaunch "${TASK1_LAUNCH}" \
  session_name:="${session_name}" \
  record_bag:=true \
  use_scan_enhancer:="${use_scan_enhancer}" \
  mapping_scan_topic:="${mapping_scan_topic}" \
  scan_enhancer_param_file:="${scan_param_file}" \
  "$@"
