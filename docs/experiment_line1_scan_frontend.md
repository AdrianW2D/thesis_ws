# Experiment Line 1: Scan Frontend Baseline vs Enhanced

## Goal

第一条实验线用于比较：

- baseline：Task1 / Task2 直接消费平台原始 `/scan`
- enhanced：Task1 / Task2 先经过 thesis 的扫描增强前端，再消费 `/scan_thesis`

这条实验线不是直接修改 gmapping、AMCL 或 move_base，而是在 thesis_ws 内增加自己的感知前端层，并观察它对建图与导航可用性的影响。

## Thesis-owned assets

- 算法包：`src/thesis_algorithms/`
- 前端节点：`src/thesis_algorithms/scripts/scan_enhancer_node.py`
- launch 封装：`launch/platform/thesis_scan_frontend.launch`
- 参数 overlay：
  - `config/overlays/sensing/scan_enhancer_baseline.yaml`
  - `config/overlays/sensing/scan_enhancer_enhanced.yaml`
- 结果模板初始化脚本：`scripts/init_line1_scan_frontend_record.sh`
- Task1 启动脚本：`scripts/run_task1_scan_frontend_experiment.sh`
- Task2 启动脚本：`scripts/run_task2_scan_frontend_experiment.sh`

## Fixed comparison rule

做 baseline / enhanced 对比时，以下条件必须保持不变：

- 同一路线建图
- 同一场地
- 同一操作者
- 同一初始定位校准方式
- 同一批单点导航测试目标
- 同一张活动地图用于 Task2 验证

只有扫描前端是否启用、以及其参数文件不同。

## Recording workflow

建议先初始化总对比模板：

```bash
"$HOME/thesis_ws/scripts/init_line1_scan_frontend_record.sh" exp_line1_lab_v01
```

然后分别执行：

```bash
"$HOME/thesis_ws/scripts/run_task1_scan_frontend_experiment.sh" baseline exp_line1_task1_baseline
"$HOME/thesis_ws/scripts/run_task1_scan_frontend_experiment.sh" enhanced exp_line1_task1_enhanced
```

再做 Task2 验证：

```bash
"$HOME/thesis_ws/scripts/run_task2_scan_frontend_experiment.sh" baseline exp_line1_task2_baseline
"$HOME/thesis_ws/scripts/run_task2_scan_frontend_experiment.sh" enhanced exp_line1_task2_enhanced
```

上述脚本会自动在：

- `results/mapping/`
- `results/navigation/`

初始化每次实验的最小记录文件，便于后续回填。

## Recommended metrics

### Task1 mapping

- `mapping_duration_sec`
- `map_usable_for_task2`
- `wall_continuity_score_1_5`
- `ghosting_score_1_5`
- `corner_closure_score_1_5`

### Task2 validation

- `target_count`
- `success_count`
- `failure_count`
- `avg_completion_time_sec`
- `initial_pose_reset_count`
- `manual_intervention_count`
- `amcl_stability_score_1_5`

## Why this comparison is valid

- Task1 负责生成地图，Task2 负责验证该地图与定位导航链是否仍可用。
- 如果增强前端只能让地图“看起来更平滑”，但 Task2 验证不通过，那么结论不能算成立。
- 因此第一条实验线要求“建图结果”和“导航验证”一起成对记录。
