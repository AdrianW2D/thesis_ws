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

- `check_dda7d0c_material_prep.sh`：`dda7d0c` 版本素材采集前置检查脚本，用于确认版本、活动地图、关键任务文件和实验脚本是否齐全
- `save_task1_map.sh`：将地图保存到 `maps/generated/`，并在 `results/mapping/` 中生成最小结果说明
- `run_task2_active_map.sh`：读取 `config/maps/map_refs.yaml` 中的 `active_map_id`，解析当前地图后启动 Task2 正式场景入口
- `run_task1_scan_frontend_experiment.sh`：第一条实验线的 Task1 启动脚本，按 `baseline/enhanced` 启动建图并初始化结果记录
- `run_task2_scan_frontend_experiment.sh`：第一条实验线的 Task2 验证脚本，按 `baseline/enhanced` 启动导航验证并初始化结果记录
- `init_line1_scan_frontend_record.sh`：生成第一条实验线的 baseline/enhanced 对比模板，便于汇总建图与导航验证结果
- `run_task3_execution_experiment.sh`：第二条实验线的统一入口，按 `baseline/enhanced` 切换任务级执行增强参数并启动 Task3 场景
- `init_line2_execution_record.sh`：生成第二条实验线的 baseline/enhanced 对比模板，便于汇总单点与巡检任务执行结果
- `run_task3_active_map.sh`：读取 `config/maps/map_refs.yaml` 中的 `active_map_id`，解析当前地图并加载 smoke patrol 任务后启动 Task3 A1 场景入口
- `run_task3_waypoint_capture_active_map.sh`：读取当前活动地图，复用 Task2 的 RViz 取点模式，并把每次 `2D Nav Goal` 点击自动保存为 Task3 waypoint YAML
- `generate_task3_coverage_task.sh`：读取矩形 coverage 配置并生成弓形 waypoint YAML，供 Task3 正式入口直接执行

推荐配套文档：

- `docs/dda7d0c_material_collection_guide.md`：`dda7d0c` 主线版本的完整素材采集指南，覆盖 Task1 / Task2 / Task3 和 line2 的实际测试流程
- `docs/task3_coverage_material_collection_guide.md`：Task3 弓形覆盖生成、执行验证与论文素材收集指南
- `docs/line1_line2_coverage_material_collection_guide.md`：line1、line2 和弓形覆盖三类实验的统一采集顺序指南
