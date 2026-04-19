# thesis_ws/src

`src/` 目前只建立 thesis 侧最小 ROS 包边界，不承载完整业务逻辑。

当前建议的最小模块如下：

- `thesis_bringup`：系统启动封装层，负责 thesis 正式入口和 reference 接入封装。
- `thesis_tasks`：任务点配置层，负责 waypoint 数据约束与后续巡检任务装载。
- `thesis_recording`：实验记录层，负责 bag、日志、结果摘要与简单评测沉淀。

第一轮阶段中，这些包只做职责占位，不实现完整节点。
