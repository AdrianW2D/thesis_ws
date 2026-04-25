# `dda7d0c` 素材采集指南

本指南面向已经更新到主线 `dda7d0c` 的工控机工作空间，用于组织一套可复现的素材采集流程，覆盖：

- Task1 地图确认或重建
- Task2 定位 + 单点导航素材
- Task3 waypoint 取点
- Task3 A1 巡检执行
- line2 baseline / enhanced 对比

这版最需要重点验证的新行为是：

- Task3 patrol 场景默认启动 RViz
- Task3 patrol 在 dispatch waypoint 前，必须等待：
  - `/move_base`
  - 第一条 `/amcl_pose`
  - 一次手工 `/initialpose`
  - `/initialpose` 后刷新的一条 `/amcl_pose`
- Task3 waypoint capture 仍然只是取点模式，不启动 `move_base`，不能直接用于执行巡检

## 0. 预检查

建议先运行一次 preflight：

```bash
"$HOME/thesis_ws/scripts/check_dda7d0c_material_prep.sh"
```

它会检查：

- 当前版本是否为 `dda7d0c`
- `task1_lab_v02` 地图是否存在
- `config/maps/map_refs.yaml` 当前 `active_map_id`
- 关键脚本和 line2 参数文件是否齐全
- `2026_4.yaml` 是否已存在

所有终端统一先执行：

```bash
source /opt/ros/melodic/setup.bash
source "$HOME/catkin_ws/devel/setup.bash"
cd "$HOME/thesis_ws"
catkin_make
source "$HOME/thesis_ws/devel/setup.bash"
```

版本确认：

```bash
cd "$HOME/thesis_ws"
git rev-parse --short HEAD
```

预期输出：

```bash
dda7d0c
```

## 1. Task1 地图确认或重建

默认工作地图使用 `task1_lab_v02`。先检查地图是否存在：

```bash
ls -l "$HOME/thesis_ws/maps/generated/task1_lab_v02.yaml"
```

如果不存在，则执行一次 Task1 建图并保存地图。

启动建图：

```bash
"$HOME/thesis_ws/scripts/run_task1_scan_frontend_experiment.sh" baseline task1_material_baseline
```

建图结束后保存：

```bash
"$HOME/thesis_ws/scripts/save_task1_map.sh" task1_lab_v02
```

然后登记地图索引：

```bash
nano "$HOME/thesis_ws/config/maps/map_refs.yaml"
```

至少要满足：

- `active_map_id: "task1_lab_v02"`
- `maps:` 下存在 `task1_lab_v02` 条目
- `runtime_map_path` 指向：
  - `"$HOME/thesis_ws/maps/generated/task1_lab_v02.yaml"`

登记后确认：

```bash
grep -n "active_map_id" "$HOME/thesis_ws/config/maps/map_refs.yaml"
grep -n "task1_lab_v02" "$HOME/thesis_ws/config/maps/map_refs.yaml"
```

建议保留素材：

- 建图 RViz 截图
- `task1_lab_v02.yaml` / `task1_lab_v02.pgm`
- `results/mapping/task1_lab_v02.md`

## 2. Task2 定位 + 单点导航素材

启动 Task2：

```bash
"$HOME/thesis_ws/scripts/run_task2_active_map.sh"
```

在 RViz 中按顺序操作：

1. 用 `2D Pose Estimate` 做姿态校准
2. 观察激光轮廓与地图对齐
3. 用 `2D Nav Goal` 发送至少 2 个单点目标
4. 记录一次成功到达过程

另开一个终端确认导航链真的活着：

```bash
source /opt/ros/melodic/setup.bash
source "$HOME/catkin_ws/devel/setup.bash"
source "$HOME/thesis_ws/devel/setup.bash"

rosnode list | grep -E "move_base|amcl|map_server"
rostopic list | grep "^/move_base"
```

预期至少包含：

- `/amcl`
- `/map_server`
- `/move_base`

建议保留素材：

- 姿态校准截图
- 全局/局部路径截图
- `results/navigation/` 下的本次记录文件

不要关闭这个 Task2 会话，后面给 Task3 复用时可作为对照。

## 3. Task3 waypoint 取点

单独打开一个新终端，启动 capture 模式，输出文件固定使用当前任务文件：

```bash
source /opt/ros/melodic/setup.bash
source "$HOME/catkin_ws/devel/setup.bash"
source "$HOME/thesis_ws/devel/setup.bash"

export THESIS_TASK3_CAPTURE_FILE="$HOME/thesis_ws/tasks/waypoint_sets/2026_4.yaml"
"$HOME/thesis_ws/scripts/run_task3_waypoint_capture_active_map.sh"
```

预期终端中出现：

- `Captured waypoints will be written to: /home/agilex/thesis_ws/tasks/waypoint_sets/2026_4.yaml`
- `Waypoint capture node ready.`

在 RViz 中：

1. 先做一次 `2D Pose Estimate`
2. 再使用 `2D Nav Goal` 点击 2 到 3 个 waypoint
3. 每点击一次，终端应出现：
   - `Captured P01 ...`
   - `Captured P02 ...`

结束 capture 会话时，在启动终端里按 `Ctrl-C`，不要直接关窗口。

结束后检查文件：

```bash
ls -l "$HOME/thesis_ws/tasks/waypoint_sets/2026_4.yaml"
cat "$HOME/thesis_ws/tasks/waypoint_sets/2026_4.yaml"
```

要求：

- 文件存在
- `map_id` 为 `task1_lab_v02`
- `points` 至少 2 个
- 每个点有 `x / y / yaw`

重要约束：

- capture 模式只用于取点
- capture 模式不会启动 `move_base`
- 不要在 capture 会话上直接执行 Task3 巡检

## 4. Task3 正式执行素材

使用正式 Task3 patrol 场景，而不是 capture 场景：

```bash
source /opt/ros/melodic/setup.bash
source "$HOME/catkin_ws/devel/setup.bash"
source "$HOME/thesis_ws/devel/setup.bash"

THESIS_TASK3_TASK_FILE="$HOME/thesis_ws/tasks/waypoint_sets/2026_4.yaml" \
"$HOME/thesis_ws/scripts/run_task3_active_map.sh"
```

`dda7d0c` 版本的关键观测点是 ready gate。启动后，终端应出现类似日志：

- `Waiting for /move_base action server`
- `Received first /amcl_pose`
- `Waiting for manual /initialpose confirmation`
- `Received /initialpose confirmation`
- `Ready gate passed after /initialpose`

在 RViz 中必须按这个顺序操作：

1. 等 RViz 打开
2. 用 `2D Pose Estimate` 做一次姿态校准
3. 等日志出现 `Ready gate passed after /initialpose`
4. 再观察 Task3 自动 dispatch waypoint

执行过程中观察：

- 机器人是否开始沿 waypoint 移动
- 是否能完成至少 1 个 waypoint
- 是否在 `results/patrol/` 生成本次 session 的 `.md` 和 `.yaml`

结束后检查：

```bash
ls -lt "$HOME/thesis_ws/results/patrol" | head
```

再打开最新结果：

```bash
cat "$HOME/thesis_ws/results/patrol/"*.md
```

建议保留素材：

- `Waiting for manual /initialpose confirmation` 日志截图
- `Ready gate passed after /initialpose` 日志截图
- Task3 自动巡检路径截图
- 对应 summary `.md` 与 `.yaml`

## 5. line2 对比素材采集

先初始化 line2 对比模板：

```bash
"$HOME/thesis_ws/scripts/init_line2_execution_record.sh" exp_line2_lab_v02
```

### 5.1 单点对比

baseline：

```bash
"$HOME/thesis_ws/scripts/run_task3_execution_experiment.sh" baseline \
  "$HOME/thesis_ws/tasks/waypoint_sets/single_goal_smoke_v01.yaml" \
  line2_single_goal_baseline
```

enhanced：

```bash
"$HOME/thesis_ws/scripts/run_task3_execution_experiment.sh" enhanced \
  "$HOME/thesis_ws/tasks/waypoint_sets/single_goal_smoke_v01.yaml" \
  line2_single_goal_enhanced
```

要求：

- 两次都完成 `/initialpose` 流程
- 两次都生成 `results/patrol/` 下的 `.md` 和 `.yaml`
- 对比以下指标是否被记录：
  - `retry_count`
  - `timeout_count`
  - `stall_count`
  - `accepted_by_thesis_count`

### 5.2 巡检对比

baseline：

```bash
"$HOME/thesis_ws/scripts/run_task3_execution_experiment.sh" baseline \
  "$HOME/thesis_ws/tasks/waypoint_sets/2026_4.yaml" \
  line2_patrol_baseline
```

enhanced：

```bash
"$HOME/thesis_ws/scripts/run_task3_execution_experiment.sh" enhanced \
  "$HOME/thesis_ws/tasks/waypoint_sets/2026_4.yaml" \
  line2_patrol_enhanced
```

要求：

- 使用同一份 `2026_4.yaml`
- 使用同一张地图 `task1_lab_v02`
- 两次都完成 `/initialpose` 后再 dispatch
- 两次都保留结果摘要

最终补充 `exp_line2_lab_v02_comparison.md` 中的对比项。

## 6. 常见问题快速判断

### 没生成 `2026_4.yaml`

优先检查：

- 是否正确 source 环境
- 启动终端里是否出现：
  - `Waypoint capture node ready.`
  - `Captured P01 ...`
- 是否在启动终端里用 `Ctrl-C` 正常退出

### `Timed out waiting for /move_base action server`

说明当前不是 patrol 执行会话，而是：

- 只起了 capture 会话，或
- 导航链根本没起来

先检查：

```bash
rosnode list | grep -E "move_base|amcl|map_server"
```

如果没有 `/move_base`，就不要继续跑 Task3 patrol。

### 一直停在 `Waiting for manual /initialpose confirmation`

说明你还没有在 RViz 中使用 `2D Pose Estimate`，或者点击后没有观察到刷新后的 `/amcl_pose`。

### 有绿色路径但不前进

先确认：

- 当前运行的是 Task3 patrol，不是 capture
- `Ready gate passed after /initialpose` 已经出现
- `/move_base` 节点确实存在

再去看：

```bash
rostopic echo -n 5 /move_base/status
rostopic echo -n 5 /cmd_vel
```

## 验收标准

### Task1

- `task1_lab_v02.yaml` / `.pgm` 已存在
- `map_refs.yaml` 已切换到 `task1_lab_v02`
- 建图结果说明文件已生成

### Task2

- `/move_base`、`/amcl`、`/map_server` 全部存在
- 至少完成 2 次单点导航
- 有姿态校准截图和路径截图

### Task3 capture

- `2026_4.yaml` 成功生成
- 文件包含至少 2 个有效 waypoint
- capture 会话已完整退出

### Task3 patrol

- patrol 场景会自动打开 RViz
- 日志中明确等待 `/initialpose`
- 做完 `2D Pose Estimate` 后日志进入 `Ready gate passed after /initialpose`
- 至少完成 1 个 waypoint
- `results/patrol/` 生成对应 `.md` 和 `.yaml`

### line2

- baseline / enhanced 各跑完一次单点和一次巡检
- 四次运行都有独立 session label
- 四次运行都生成结果摘要
- 对比模板已填入核心指标
