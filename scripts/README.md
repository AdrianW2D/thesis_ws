# scripts

这里预留 thesis 侧实验辅助脚本。

适合放入的内容：

- 结果整理小脚本
- waypoint 数据检查脚本
- bag 与日志整理脚本
- Task1 地图保存脚本

不适合放入的内容：

- 底层驱动逻辑
- 平台传感器接入逻辑
- 大型业务实现

当前已提供：

- `save_task1_map.sh`：将地图保存到 `maps/generated/`，并在 `results/mapping/` 中生成最小结果说明
- `run_task2_active_map.sh`：读取 `config/maps/map_refs.yaml` 中的 `active_map_id`，解析当前地图后启动 Task2 正式场景入口
- `run_task1_scan_frontend_experiment.sh`：第一条实验线的 Task1 启动脚本，按 `baseline/enhanced` 启动建图并初始化结果记录
- `run_task2_scan_frontend_experiment.sh`：第一条实验线的 Task2 验证脚本，按 `baseline/enhanced` 启动导航验证并初始化结果记录
- `init_line1_scan_frontend_record.sh`：生成第一条实验线的 baseline/enhanced 对比模板，便于汇总建图与导航验证结果
- `run_task3_execution_experiment.sh`：第二条实验线的统一入口，按 `baseline/enhanced` 切换任务级执行增强参数并启动 Task3 场景
- `init_line2_execution_record.sh`：生成第二条实验线的 baseline/enhanced 对比模板，便于汇总单点与巡检任务执行结果
- `run_task3_active_map.sh`：读取 `config/maps/map_refs.yaml` 中的 `active_map_id`，解析当前地图并加载 smoke patrol 任务后启动 Task3 A1 场景入口
- `run_task3_waypoint_capture_active_map.sh`：读取当前活动地图，复用 Task2 的 RViz 取点模式，并把每次 `2D Nav Goal` 点击自动保存为 Task3 waypoint YAML
