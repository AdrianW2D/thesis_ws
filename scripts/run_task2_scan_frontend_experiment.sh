#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THESIS_WS="$(cd "${SCRIPT_DIR}/.." && pwd)"
TASK2_SCRIPT="${THESIS_TASK2_SCRIPT:-${THESIS_WS}/scripts/run_task2_active_map.sh}"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <baseline|enhanced> [session_name] [extra launch args...]" >&2
  exit 1
fi

mode="$1"
shift

if [[ "${mode}" != "baseline" && "${mode}" != "enhanced" ]]; then
  echo "mode must be baseline or enhanced" >&2
  exit 1
fi

session_name="${1:-line1_task2_${mode}_$(date +%Y%m%d_%H%M%S)}"
if [[ $# -gt 0 ]]; then
  shift
fi

if [[ ! -x "${TASK2_SCRIPT}" ]]; then
  echo "Task2 launcher not executable: ${TASK2_SCRIPT}" >&2
  exit 1
fi

use_scan_enhancer="false"
nav_scan_topic="/scan"
scan_param_file="${THESIS_WS}/config/overlays/sensing/scan_enhancer_baseline.yaml"

if [[ "${mode}" == "enhanced" ]]; then
  use_scan_enhancer="true"
  nav_scan_topic="/scan_thesis"
  scan_param_file="${THESIS_WS}/config/overlays/sensing/scan_enhancer_enhanced.yaml"
fi

result_note="${THESIS_WS}/results/navigation/${session_name}.md"
mkdir -p "$(dirname "${result_note}")"

cat > "${result_note}" <<EOF
# ${session_name}

- experiment_line: line1_scan_frontend
- task: task2_single_goal_navigation_validation
- variant: ${mode}
- session_name: ${session_name}
- scan_input_topic: /scan
- nav_scan_topic: ${nav_scan_topic}
- scan_enhancer_enabled: ${use_scan_enhancer}
- scan_enhancer_param_file: ${scan_param_file#${THESIS_WS}/}
- bag_path: bags/navigation/${session_name}.bag

## Metrics

| item | value | note |
| --- | --- | --- |
| active_map_id |  |  |
| initial_pose_reset_count |  | manual count |
| target_count |  |  |
| success_count |  |  |
| failure_count |  |  |
| avg_completion_time_sec |  |  |
| manual_intervention_count |  |  |
| amcl_stability_score_1_5 |  | manual score |
| operator_note |  |  |

## Screenshot checklist

- [ ] AMCL pose / particle screenshot saved
- [ ] global/local plan screenshot saved
- [ ] failures or relocalization notes saved
EOF

echo "Launching Task2 scan-frontend experiment: mode=${mode} session=${session_name}"
echo "Initialized result note: ${result_note}"

exec "${TASK2_SCRIPT}" \
  session_name:="${session_name}" \
  record_bag:=true \
  use_scan_enhancer:="${use_scan_enhancer}" \
  nav_scan_topic:="${nav_scan_topic}" \
  scan_enhancer_param_file:="${scan_param_file}" \
  "$@"
