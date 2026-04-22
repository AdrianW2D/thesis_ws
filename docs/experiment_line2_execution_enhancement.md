# Experiment Line 2: Navigation Execution Baseline vs Enhanced

## Goal

第二条实验线用于比较：

- baseline：目标点直接交给 `move_base`，仅依赖默认结果返回
- enhanced：由 thesis 的任务执行器接管目标执行过程，并增加阶段执行、进度监测、卡滞恢复和 thesis 自主接受判定

这条实验线不修改 `move_base` 内核，而是在 thesis_ws 内增加自己的任务级执行增强层。

Task3 当前默认会启动 RViz，并在收到一次手工 `2D Pose Estimate` 之后才开始自动下发 waypoint。这样可以避免 AMCL 尚未校准时，任务执行器过早发送目标，出现“全局路径已规划但底盘不前进”的假启动现象。

## Thesis-owned assets

- 执行节点：`src/thesis_tasks/scripts/task_manager_node.py`
- 场景入口：`launch/scenarios/task3_patrol_stub.launch`
- baseline 参数：`config/tasks/patrol_manager_line2_baseline.yaml`
- enhanced 参数：`config/tasks/patrol_manager_line2_enhanced.yaml`
- 对比模板：`scripts/init_line2_execution_record.sh`
- 统一启动脚本：`scripts/run_task3_execution_experiment.sh`
- 单点任务文件：`tasks/waypoint_sets/single_goal_smoke_v01.yaml`
- 巡检任务文件：`tasks/waypoint_sets/patrol_smoke_v01.yaml`

## Enhanced execution features

增强模式当前具备：

- 两阶段目标执行：
  - `approach`：先到达目标附近
  - `align`：再完成最终姿态对齐
- 进度监测：
  - 检查距离目标是否持续缩小
- 卡滞检测：
  - 在 progress_timeout 时间内未达到最小位移改进则判定 stalled
- 恢复机制：
  - cancel 当前 goal
  - retry 当前 stage
  - 达上限后按 `skip_on_failure` 决定跳过或终止
- thesis 自主接受判定：
  - 即使 `move_base` 未返回 `SUCCEEDED`，只要位姿误差已落入 thesis 设定阈值，也可记为 `accepted_by_thesis`
- 双格式结果摘要：
  - Markdown 摘要
  - YAML 结构化摘要

## Recording workflow

建议先初始化总对比模板：

```bash
"$HOME/thesis_ws/scripts/init_line2_execution_record.sh" exp_line2_lab_v01
```

### Single-goal style validation

```bash
"$HOME/thesis_ws/scripts/run_task3_execution_experiment.sh" baseline \
  "$HOME/thesis_ws/tasks/waypoint_sets/single_goal_smoke_v01.yaml" \
  line2_single_goal_baseline

"$HOME/thesis_ws/scripts/run_task3_execution_experiment.sh" enhanced \
  "$HOME/thesis_ws/tasks/waypoint_sets/single_goal_smoke_v01.yaml" \
  line2_single_goal_enhanced
```

### Patrol validation

```bash
"$HOME/thesis_ws/scripts/run_task3_execution_experiment.sh" baseline \
  "$HOME/thesis_ws/tasks/waypoint_sets/patrol_smoke_v01.yaml" \
  line2_patrol_baseline

"$HOME/thesis_ws/scripts/run_task3_execution_experiment.sh" enhanced \
  "$HOME/thesis_ws/tasks/waypoint_sets/patrol_smoke_v01.yaml" \
  line2_patrol_enhanced
```

## Recommended metrics

### Single goal

- `success_count`
- `failure_count`
- `avg_completion_time_sec`
- `timeout_count`
- `retry_count`
- `manual_intervention_count`

### Patrol

- `waypoint_total`
- `waypoint_success_count`
- `waypoint_skip_count`
- `waypoint_failure_count`
- `task_completed`
- `task_total_time_sec`
- `avg_waypoint_time_sec`
- `recovery_trigger_count`
- `accepted_by_thesis_count`
- `manual_takeover_count`

## Why this comparison is valid

- baseline 与 enhanced 使用相同地图、相同任务文件和相同平台导航链
- 唯一差异是 thesis 任务执行器的策略与恢复逻辑
- 因此可以将结果差异归因于 thesis 自己的任务级执行增强机制
