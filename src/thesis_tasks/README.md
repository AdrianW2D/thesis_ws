# thesis_tasks

本包用于 thesis 侧任务组织层。

当前已具备的 A1 基础：

- 定义 waypoint / patrol task 的数据组织方式
- 约束任务点命名、字段、文件落位
- 提供 `task_manager_node.py` 最小巡检执行器
- 支持 waypoint 装载、ready gate、move_base 顺序执行、重试/跳过与最小 session 摘要
- 提供 `coverage_path_generator.py`，把矩形 coverage 配置离线转换成可直接执行的 waypoint YAML

当前阶段仍然不做：

- 多节点拆分
- 自定义 msg/srv
- 复杂策略优化
- 在线覆盖规划或任意多边形区域规划
