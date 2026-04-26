# coverage_sets

这里放 thesis 侧“区域覆盖任务”的输入配置，而不是最终执行的 waypoint 队列。

当前约定：

- `coverage_sets/`：规则区域覆盖任务配置
- `waypoint_sets/`：由 coverage generator 生成、并可直接交给 Task3 执行器的 waypoint YAML

第一版范围控制：

- 只支持矩形区域
- 只支持离线生成
- 只生成弓形往返的 waypoint 序列
- 不做在线重规划
- 不做任意多边形
- 不改 `catkin_ws`
