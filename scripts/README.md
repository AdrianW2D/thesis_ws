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
