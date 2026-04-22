#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THESIS_WS="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULT_ROOT="${THESIS_WS}/results"

experiment_id="${1:-line1_$(date +%Y%m%d_%H%M%S)}"
output_file="${RESULT_ROOT}/mapping/${experiment_id}_comparison.md"

mkdir -p "$(dirname "${output_file}")" "${RESULT_ROOT}/navigation"

cat > "${output_file}" <<EOF
# ${experiment_id} - Scan Frontend Comparison

- experiment_line: line1_scan_frontend
- purpose: compare baseline raw scan pipeline with thesis scan enhancement frontend
- map_route_note: fill before experiments
- operator: fill before experiments

## Mapping Comparison

| metric | baseline | enhanced | note |
| --- | --- | --- | --- |
| map_name |  |  |  |
| mapping_duration_sec |  |  |  |
| map_usable_for_task2 |  |  |  |
| wall_continuity_score_1_5 |  |  | higher is better |
| ghosting_score_1_5 |  |  | lower is better |
| corner_closure_score_1_5 |  |  | higher is better |

## Task2 Validation Comparison

| metric | baseline | enhanced | note |
| --- | --- | --- | --- |
| active_map_id |  |  |  |
| target_count |  |  |  |
| success_count |  |  |  |
| failure_count |  |  |  |
| avg_completion_time_sec |  |  |  |
| initial_pose_reset_count |  |  | lower is better |
| manual_intervention_count |  |  | lower is better |
| amcl_stability_score_1_5 |  |  | higher is better |

## Linked Session Notes

- baseline_task1_note: results/mapping/
- enhanced_task1_note: results/mapping/
- baseline_task2_note: results/navigation/
- enhanced_task2_note: results/navigation/

## Conclusion

- summary:
- keep / reject / revise:
- next change:
EOF

echo "Created comparison template: ${output_file}"
