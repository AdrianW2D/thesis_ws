#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THESIS_WS="$(cd "${SCRIPT_DIR}/.." && pwd)"
RESULT_ROOT="${THESIS_WS}/results/patrol"

experiment_id="${1:-line2_$(date +%Y%m%d_%H%M%S)}"
output_file="${RESULT_ROOT}/${experiment_id}_comparison.md"

mkdir -p "${RESULT_ROOT}"

cat > "${output_file}" <<EOF
# ${experiment_id} - Navigation Execution Comparison

- experiment_line: line2_execution_enhancement
- purpose: compare baseline goal execution with thesis enhanced task execution
- task_file_note: fill before experiments
- operator: fill before experiments

## Single Goal Comparison

| metric | baseline | enhanced | note |
| --- | --- | --- | --- |
| task_file |  |  |  |
| success_count |  |  |  |
| failure_count |  |  |  |
| avg_completion_time_sec |  |  |  |
| timeout_count |  |  | lower is better |
| retry_count |  |  | lower is better |
| manual_intervention_count |  |  | lower is better |

## Patrol Comparison

| metric | baseline | enhanced | note |
| --- | --- | --- | --- |
| waypoint_total |  |  |  |
| waypoint_success_count |  |  |  |
| waypoint_skip_count |  |  | lower is better |
| waypoint_failure_count |  |  | lower is better |
| task_completed |  |  | yes/no |
| task_total_time_sec |  |  |  |
| avg_waypoint_time_sec |  |  |  |
| recovery_trigger_count |  |  | reflects recovery behavior |
| accepted_by_thesis_count |  |  | enhanced only |
| manual_takeover_count |  |  | lower is better |

## Linked Summaries

- baseline_summary_md:
- baseline_summary_yaml:
- enhanced_summary_md:
- enhanced_summary_yaml:

## Conclusion

- summary:
- keep / reject / revise:
- next change:
EOF

echo "Created comparison template: ${output_file}"
