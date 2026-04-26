# tasks

这里放 thesis 侧的任务定义文件，而不是底层平台包。

当前阶段只建立“任务点/标记点”数据组织方式：

- `waypoint_sets/`：多点巡检任务点集合
- `coverage_sets/`：矩形区域覆盖任务配置，供 thesis 侧 coverage generator 生成 waypoint
- 任务文件只描述数据，不实现执行器
- Task3 A1 直接从 `waypoint_sets/` 读取 waypoint 队列
- Task3 后续覆盖能力先从 `coverage_sets/` 生成 waypoint，再复用现有 Task3 执行器
