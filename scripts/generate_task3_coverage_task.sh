#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THESIS_WS="$(cd "${SCRIPT_DIR}/.." && pwd)"
GENERATOR_SCRIPT="${THESIS_COVERAGE_GENERATOR:-${THESIS_WS}/src/thesis_tasks/scripts/coverage_path_generator.py}"
CONFIG_FILE="${THESIS_COVERAGE_CONFIG:-${THESIS_WS}/tasks/coverage_sets/coverage_rect_smoke_v01.yaml}"
OUTPUT_FILE="${THESIS_COVERAGE_OUTPUT:-}"

if [[ $# -ge 1 ]]; then
  CONFIG_FILE="$1"
  shift
fi

if [[ $# -ge 1 ]]; then
  OUTPUT_FILE="$1"
  shift
fi

PYTHON_CMD=""
if command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
else
  echo "Neither python nor python3 was found. Install Python before generating coverage tasks." >&2
  exit 1
fi

if [[ ! -f "${GENERATOR_SCRIPT}" ]]; then
  echo "Coverage generator not found: ${GENERATOR_SCRIPT}" >&2
  exit 1
fi

if [[ ! -f "${CONFIG_FILE}" ]]; then
  echo "Coverage config not found: ${CONFIG_FILE}" >&2
  exit 1
fi

cmd=("${PYTHON_CMD}" "${GENERATOR_SCRIPT}" --config "${CONFIG_FILE}" --overwrite)
if [[ -n "${OUTPUT_FILE}" ]]; then
  cmd+=(--output "${OUTPUT_FILE}")
fi
if [[ $# -gt 0 ]]; then
  cmd+=("$@")
fi

echo "Generating Task3 coverage waypoint task"
echo "  python: ${PYTHON_CMD}"
echo "  config: ${CONFIG_FILE}"
if [[ -n "${OUTPUT_FILE}" ]]; then
  echo "  output override: ${OUTPUT_FILE}"
fi

exec "${cmd[@]}"
