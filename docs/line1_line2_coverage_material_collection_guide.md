# line1 + line2 + 弓形覆盖 总测试与素材采集指南

本指南用于一次性组织 thesis_ws 当前三类核心实验任务的测试与论文素材采集：

- line1：扫描前端增强对比
- line2：任务级导航执行增强对比
- 弓形覆盖：矩形区域 coverage 生成与执行验证

这份指南的目标不是介绍所有架构细节，而是给出一条可直接执行的采集顺序，保证：

1. 地图、定位、导航前提一致
2. baseline / enhanced 对比口径一致
3. coverage 任务能复用现有 Task3 执行链
4. 论文方法图、过程图、结果图都能一次性留齐

## 0. 前置检查

所有终端统一先执行：

```bash
source /opt/ros/melodic/setup.bash
source "$HOME/catkin_ws/devel/setup.bash"
cd "$HOME/thesis_ws"
catkin_make
source "$HOME/thesis_ws/devel/setup.bash"
```

建议先跑一次总 preflight：

```bash
"$HOME/thesis_ws/scripts/check_dda7d0c_material_prep.sh"
```

最低前提：

- `config/maps/map_refs.yaml` 中 `active_map_id` 指向当前实验地图
- 目标地图文件存在，例如 `task1_lab_v02`
- Task2 可正常启动并完成单点导航
- Task3 A1 可正常进入 `/initialpose` ready gate

## 1. 推荐整体采集顺序

推荐严格按这个顺序执行：

1. 先确认或重建地图
2. 做 line1 的 Task1 baseline / enhanced
3. 做 line1 的 Task2 baseline / enhanced
4. 做 Task3 waypoint capture，得到一份真实巡检任务文件
5. 做 line2 的单点 baseline / enhanced
6. 做 line2 的巡检 baseline / enhanced
7. 做 coverage 角点采集
8. 生成 coverage waypoint 文件
9. 跑 coverage 巡检
10. 如果需要，再跑 coverage 的 line2 baseline / enhanced

这样安排的原因：

- line1 要先把地图和感知前端对比做完整
- line2 要建立在“地图可用、定位可用、Task3 patrol 主链可用”之上
- coverage 是在 Task3 基础上再加一层任务生成，不应先于 line2

## 2. 地图确认或重建

先检查地图是否存在：

```bash
ls -l "$HOME/thesis_ws/maps/generated/task1_lab_v02.yaml"
```

如果不存在，先重建：

```bash
"$HOME/thesis_ws/scripts/run_task1_scan_frontend_experiment.sh" baseline task1_material_baseline
"$HOME/thesis_ws/scripts/save_task1_map.sh" task1_lab_v02
```

然后确认地图索引：

```bash
grep -n "active_map_id" "$HOME/thesis_ws/config/maps/map_refs.yaml"
grep -n "task1_lab_v02" "$HOME/thesis_ws/config/maps/map_refs.yaml"
```

建议保留素材：

- 建图 RViz 截图
- `task1_lab_v02.yaml`
- `task1_lab_v02.pgm`
- `results/mapping/task1_lab_v02.md`

## 3. line1：扫描前端增强对比

line1 的完整说明在：

- `docs/experiment_line1_scan_frontend.md`

这里按素材采集口径直接执行。

### 3.1 初始化 line1 对比模板

```bash
"$HOME/thesis_ws/scripts/init_line1_scan_frontend_record.sh" exp_line1_lab_v02
```

### 3.2 Task1 baseline / enhanced

baseline：

```bash
"$HOME/thesis_ws/scripts/run_task1_scan_frontend_experiment.sh" baseline exp_line1_task1_baseline
```

enhanced：

```bash
"$HOME/thesis_ws/scripts/run_task1_scan_frontend_experiment.sh" enhanced exp_line1_task1_enhanced
```

采集重点：

- 地图边界连续性
- 墙面是否更平滑
- 转角闭合情况
- 是否出现 ghosting

建议保留素材：

- baseline 地图截图
- enhanced 地图截图
- 两次 mapping 结果说明文件

### 3.3 Task2 baseline / enhanced

baseline：

```bash
"$HOME/thesis_ws/scripts/run_task2_scan_frontend_experiment.sh" baseline exp_line1_task2_baseline
```

enhanced：

```bash
"$HOME/thesis_ws/scripts/run_task2_scan_frontend_experiment.sh" enhanced exp_line1_task2_enhanced
```

每次都在 RViz 中：

1. 用 `2D Pose Estimate` 做姿态校准
2. 发至少 2 个 `2D Nav Goal`
3. 记录成功率、时间和人工干预情况

建议保留素材：

- 姿态校准截图
- 全局路径 / 局部路径截图
- baseline / enhanced 的导航记录文件

### 3.4 line1 验收

至少满足：

- line1 的 Task1 baseline / enhanced 都完成
- line1 的 Task2 baseline / enhanced 都完成
- 对比模板中已回填：
  - 地图可用性
  - 导航成功率
  - 人工干预次数

## 4. Task3 waypoint 基础任务文件准备

line2 和 coverage 都依赖真实任务文件。先准备一份巡检任务文件。

```bash
export THESIS_TASK3_CAPTURE_FILE="$HOME/thesis_ws/tasks/waypoint_sets/2026_4.yaml"
"$HOME/thesis_ws/scripts/run_task3_waypoint_capture_active_map.sh"
```

在 RViz 中：

1. `2D Pose Estimate`
2. 用 `2D Nav Goal` 点击 2 到 3 个真实 waypoint
3. 每点一次都观察终端出现 `Captured P01 ...`
4. 在启动终端里按 `Ctrl-C` 正常退出

检查结果：

```bash
ls -l "$HOME/thesis_ws/tasks/waypoint_sets/2026_4.yaml"
cat "$HOME/thesis_ws/tasks/waypoint_sets/2026_4.yaml"
```

要求：

- `map_id` 正确
- `points` 至少 2 个
- 每个点有 `x / y / yaw`

## 5. line2：任务级导航执行增强对比

line2 的完整说明在：

- `docs/experiment_line2_execution_enhancement.md`

这里按素材采集顺序直接执行。

### 5.1 初始化 line2 对比模板

```bash
"$HOME/thesis_ws/scripts/init_line2_execution_record.sh" exp_line2_lab_v02
```

### 5.2 单点 baseline / enhanced

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

每次都要：

1. 等 RViz 打开
2. 完成一次 `2D Pose Estimate`
3. 等 `Ready gate passed after /initialpose`
4. 再观察自动执行

采集重点：

- `retry_count`
- `timeout_count`
- `stall_count`
- `accepted_by_thesis_count`

### 5.3 巡检 baseline / enhanced

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

采集重点：

- waypoint 总数
- waypoint 完成 / 跳过 / 失败数
- recovery 触发次数
- thesis 接受判定次数

建议保留素材：

- `Waiting for manual /initialpose confirmation` 日志截图
- `Ready gate passed after /initialpose` 日志截图
- baseline / enhanced 的巡检路径截图
- `results/patrol/` 生成的 `.md` 和 `.yaml`

### 5.4 line2 验收

至少满足：

- 单点 baseline / enhanced 已跑完
- 巡检 baseline / enhanced 已跑完
- 四次运行都有独立 session label
- 四次结果都已生成摘要

## 6. 弓形覆盖：coverage 生成与执行

coverage 的完整说明在：

- `docs/task3_coverage_material_collection_guide.md`

这里按素材采集顺序直接执行。

### 6.1 先采矩形区域两个角点

```bash
export THESIS_TASK3_CAPTURE_FILE="$HOME/thesis_ws/tasks/waypoint_sets/coverage_corner_capture.yaml"
"$HOME/thesis_ws/scripts/run_task3_waypoint_capture_active_map.sh"
```

在 RViz 中：

1. `2D Pose Estimate`
2. 用 `2D Nav Goal` 点击矩形的两个对角位置
3. 正常 `Ctrl-C` 退出

检查：

```bash
cat "$HOME/thesis_ws/tasks/waypoint_sets/coverage_corner_capture.yaml"
```

### 6.2 准备 coverage 配置

复制示例：

```bash
cp "$HOME/thesis_ws/tasks/coverage_sets/coverage_rect_smoke_v01.yaml" \
   "$HOME/thesis_ws/tasks/coverage_sets/coverage_lab_v01.yaml"
```

编辑：

```bash
nano "$HOME/thesis_ws/tasks/coverage_sets/coverage_lab_v01.yaml"
```

至少改：

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

### 6.3 生成 coverage waypoint 文件

```bash
"$HOME/thesis_ws/scripts/generate_task3_coverage_task.sh" \
  "$HOME/thesis_ws/tasks/coverage_sets/coverage_lab_v01.yaml"
```

如果终端提示缺少 PyYAML，先检查：

```bash
python -c "import yaml; print('yaml_ok')"
```

检查生成文件：

```bash
cat "$HOME/thesis_ws/tasks/waypoint_sets/coverage_lab_generated_v01.yaml"
```

采集重点：

- `coverage_metadata`
- lane 数
- waypoint 数
- 点位顺序是否为弓形往返

### 6.4 执行 coverage 巡检

```bash
THESIS_TASK3_TASK_FILE="$HOME/thesis_ws/tasks/waypoint_sets/coverage_lab_generated_v01.yaml" \
"$HOME/thesis_ws/scripts/run_task3_active_map.sh"
```

在 RViz 中：

1. `2D Pose Estimate`
2. 等 `Ready gate passed after /initialpose`
3. 观察机器人是否按 coverage waypoint 执行

建议保留素材：

- coverage 配置文件截图
- coverage 生成日志
- coverage waypoint YAML 截图
- coverage 巡检 RViz 截图
- 对应 patrol 摘要 `.md` / `.yaml`

### 6.5 可选：coverage 进入 line2 对比

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

如果你要把 coverage 也纳入论文对比，这一步很有价值。

## 7. 最终素材清单

建议至少整理出以下文件和截图：

### line1

- baseline / enhanced 的 Task1 地图截图
- baseline / enhanced 的 Task2 导航截图
- `results/mapping/` 与 `results/navigation/` 对应记录
- `exp_line1_lab_v02_comparison.md`

### line2

- 单点 baseline / enhanced 日志截图
- 巡检 baseline / enhanced 路径截图
- `results/patrol/` 下四次 `.md` / `.yaml`
- `exp_line2_lab_v02_comparison.md`

### coverage

- `coverage_corner_capture.yaml`
- `coverage_lab_v01.yaml`
- `coverage_lab_generated_v01.yaml`
- coverage 执行截图
- coverage patrol summary

## 8. 论文写作建议口径

如果你按这份指南跑完，论文里可以清晰拆成三部分：

1. line1：
   - thesis 自有扫描前端增强
   - 对建图与定位导航链的影响

2. line2：
   - thesis 自有任务级导航执行增强
   - 对巡检任务执行稳定性的影响

3. coverage：
   - thesis 自有区域覆盖任务生成能力
   - 从规则矩形区域自动生成弓形 waypoint，并复用现有巡检执行链完成验证

这三部分组合起来，方法层、执行层、任务层都有 thesis 自己的工作量，论文主体会更完整。
