# Task3 弓形覆盖测试与论文素材收集指南

本指南面向 thesis_ws 后续新增的“矩形区域弓形覆盖”能力。当前实现口径是：

- 不修改 `catkin_ws`
- 不重写 `move_base`
- 不做在线覆盖规划
- 只做 thesis 侧离线 coverage config -> waypoint YAML 生成
- 生成结果继续复用现有 Task3 patrol 执行链

也就是说，当前工作流固定为：

```text
coverage config
-> coverage_path_generator.py
-> waypoint task yaml
-> run_task3_active_map.sh
-> task_manager_node.py
```

## 1. 适用范围

当前第一版只支持：

- 规则矩形区域
- `x_major` 或 `y_major` 两种条带方向
- `lower_left / lower_right / upper_left / upper_right` 四种起始角
- 离线生成弓形 waypoint

当前不支持：

- 任意多边形
- 多区域组合
- 在线重规划
- 动态障碍适应覆盖
- 覆盖率最优性优化

## 2. 前置准备

所有终端统一先执行：

```bash
source /opt/ros/melodic/setup.bash
source "$HOME/catkin_ws/devel/setup.bash"
cd "$HOME/thesis_ws"
catkin_make
source "$HOME/thesis_ws/devel/setup.bash"
```

确认以下前提成立：

1. 已存在可用地图，例如 `task1_lab_v02`
2. `config/maps/map_refs.yaml` 的 `active_map_id` 指向当前实验地图
3. Task2 单点导航已可正常工作
4. Task3 A1 正式入口已可正常启动

## 3. 需要关注的文件

- coverage schema：
  - `config/tasks/coverage_schema.yaml`
- coverage 示例配置：
  - `tasks/coverage_sets/coverage_rect_smoke_v01.yaml`
- coverage 生成器：
  - `src/thesis_tasks/scripts/coverage_path_generator.py`
- 辅助脚本：
  - `scripts/generate_task3_coverage_task.sh`
- 生成后的 waypoint 任务文件默认输出到：
  - `tasks/waypoint_sets/`
- 巡检执行结果默认输出到：
  - `results/patrol/`

## 4. 如何准备真实矩形区域

最稳的方式不是直接猜坐标，而是先在当前活动地图上确认两个对角点。

推荐做法：

1. 先启动 Task3 waypoint capture：

```bash
export THESIS_TASK3_CAPTURE_FILE="$HOME/thesis_ws/tasks/waypoint_sets/coverage_corner_capture.yaml"
"$HOME/thesis_ws/scripts/run_task3_waypoint_capture_active_map.sh"
```

2. 在 RViz 中：
   - 先用 `2D Pose Estimate` 完成定位校准
   - 用 `2D Nav Goal` 依次点击矩形的两个对角位置

3. 完成后在启动终端中按 `Ctrl-C` 退出 capture

4. 查看记录下来的两个角点：

```bash
cat "$HOME/thesis_ws/tasks/waypoint_sets/coverage_corner_capture.yaml"
```

5. 用这两个点换算 coverage config：
   - `origin.x = min(x1, x2)`
   - `origin.y = min(y1, y2)`
   - `width = abs(x2 - x1)`
   - `height = abs(y2 - y1)`

这样可以避免在地图坐标上盲填。

## 5. 生成 coverage waypoint 任务

### 5.1 直接使用示例配置

先复制示例配置，再改成自己的实验区域：

```bash
cp "$HOME/thesis_ws/tasks/coverage_sets/coverage_rect_smoke_v01.yaml" \
   "$HOME/thesis_ws/tasks/coverage_sets/coverage_lab_v01.yaml"
```

编辑：

```bash
nano "$HOME/thesis_ws/tasks/coverage_sets/coverage_lab_v01.yaml"
```

至少改这些字段：

- `map_id`
- `area.origin.x`
- `area.origin.y`
- `area.width`
- `area.height`
- `sweep.direction`
- `sweep.lane_spacing`
- `sweep.boundary_margin`
- `sweep.start_corner`
- `output.task_file`

### 5.2 生成 waypoint YAML

推荐使用辅助脚本：

```bash
"$HOME/thesis_ws/scripts/generate_task3_coverage_task.sh" \
  "$HOME/thesis_ws/tasks/coverage_sets/coverage_lab_v01.yaml"
```

如果要显式覆盖输出文件：

```bash
"$HOME/thesis_ws/scripts/generate_task3_coverage_task.sh" \
  "$HOME/thesis_ws/tasks/coverage_sets/coverage_lab_v01.yaml" \
  "$HOME/thesis_ws/tasks/waypoint_sets/coverage_lab_generated_v01.yaml"
```

预期终端输出类似：

```text
Generating Task3 coverage waypoint task
  python: python
Coverage config: /home/agilex/thesis_ws/tasks/coverage_sets/coverage_lab_v01.yaml
Generated task file: /home/agilex/thesis_ws/tasks/waypoint_sets/coverage_lab_generated_v01.yaml
Sweep summary: direction=x_major, lanes=4, waypoints=8
```

### 5.3 检查生成结果

```bash
cat "$HOME/thesis_ws/tasks/waypoint_sets/coverage_lab_generated_v01.yaml"
```

重点检查：

1. `map_id` 是否正确
2. `frame_id` 是否为 `map`
3. `coverage_metadata` 是否存在
4. `points` 数量是否符合预期
5. 点位顺序是否呈现弓形往返

如果终端提示：

```text
Coverage generation failed: PyYAML is not available for the selected Python interpreter.
```

优先检查：

```bash
python -c "import yaml; print('yaml_ok')"
```

在 Ubuntu 18.04 + ROS Melodic 工控机上，通常应先正确 `source /opt/ros/melodic/setup.bash` 和工作空间环境，再执行生成脚本。

## 6. 运行 Task3 覆盖巡检

使用正式 Task3 patrol 场景执行生成后的 waypoint 任务：

```bash
THESIS_TASK3_TASK_FILE="$HOME/thesis_ws/tasks/waypoint_sets/coverage_lab_generated_v01.yaml" \
"$HOME/thesis_ws/scripts/run_task3_active_map.sh"
```

这时会走现有 Task3 正式链：

- 启动 RViz
- 等待 `/move_base`
- 等待第一条 `/amcl_pose`
- 等待一次手工 `/initialpose`
- 等待刷新后的 `/amcl_pose`
- 然后自动 dispatch coverage waypoint

在 RViz 中按顺序操作：

1. 等 RViz 打开
2. 用 `2D Pose Estimate` 做姿态校准
3. 等日志出现 `Ready gate passed after /initialpose`
4. 观察机器人是否开始按弓形 waypoint 自动巡检

## 7. 推荐测试顺序

### 阶段 A：纯生成验证

目标：
- 先证明 coverage config 能稳定生成 waypoint YAML

步骤：
1. 用示例 config 生成一份 waypoint YAML
2. 检查 lane 数和 waypoint 数
3. 确认每个点都有 `x/y/yaw`
4. 确认顺序呈现弓形往返

验收：
- 生成命令无报错
- 输出 YAML 存在
- `coverage_metadata` 合理

### 阶段 B：单次覆盖执行验证

目标：
- 证明 coverage waypoint 能被现有 Task3 执行链正常接管

步骤：
1. 用真实区域生成一份 coverage waypoint 文件
2. 启动 Task3 patrol
3. 做 `2D Pose Estimate`
4. 观察至少完成 1 条条带往返

验收：
- Task3 通过 ready gate
- 机器人开始移动
- `results/patrol/` 生成本次 `.md` 和 `.yaml` 摘要

### 阶段 C：论文素材补齐

目标：
- 留下可直接写入论文的方法图、流程图和结果图

建议保留素材：

1. coverage 配置文件截图
2. 角点采集文件截图
3. 生成后的 waypoint YAML 截图
4. RViz 中 coverage 执行截图
5. 巡检结果摘要 `.md` / `.yaml`
6. 若要做 line2 对比，再保留 baseline / enhanced 两次结果

## 8. 推荐论文素材结构

建议至少整理以下材料：

### 8.1 方法说明素材

- `coverage_schema.yaml`
- `coverage_lab_v01.yaml`
- 生成器输出日志

论文可写口径：

- 输入为规则矩形区域配置
- 中间过程为条带生成与弓形 waypoint 组织
- 输出为标准 waypoint 任务文件
- 执行层继续复用现有 Task3 patrol manager

### 8.2 实验过程素材

- coverage 角点采集过程截图
- 配置编辑截图
- waypoint 生成结果截图
- Task3 RViz 执行截图

### 8.3 实验结果素材

- `results/patrol/<session>.md`
- `results/patrol/<session>.yaml`
- 至少记录：
  - lane 数
  - waypoint 数
  - 完成点数
  - 跳过点数
  - 失败点数
  - retry / timeout / stall 统计

## 9. 可选：继续复用第二条实验线

如果要证明 coverage 任务也能进入 thesis 的执行增强链，可以继续做：

baseline：

```bash
"$HOME/thesis_ws/scripts/run_task3_execution_experiment.sh" baseline \
  "$HOME/thesis_ws/tasks/waypoint_sets/coverage_lab_generated_v01.yaml" \
  coverage_line2_baseline
```

enhanced：

```bash
"$HOME/thesis_ws/scripts/run_task3_execution_experiment.sh" enhanced \
  "$HOME/thesis_ws/tasks/waypoint_sets/coverage_lab_generated_v01.yaml" \
  coverage_line2_enhanced
```

这样论文里可以写成：

- coverage path 由 thesis 自己生成
- 执行层又可切换 thesis 自己的 baseline / enhanced 任务执行策略

## 10. 当前范围边界

本次新增能力只解决：

- 规则矩形区域
- thesis 侧弓形 waypoint 自动生成
- 与现有 Task3 patrol 执行链对接

当前不声称解决：

- 任意形状区域覆盖
- 动态障碍适应覆盖
- 最优覆盖率或最优时间规划
- 在线局部重规划

这是当前阶段的刻意范围控制，用来保证工程可落地、实验可复现、论文可收口。
