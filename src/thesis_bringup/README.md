# thesis_bringup

本包预留给 thesis 侧的系统启动封装。

第一轮只定义职责，不实现完整 launch 逻辑：

- 封装平台能力接入
- 提供 thesis 正式入口的命名边界
- 承接后续 mapping、single-goal navigation、patrol 三类实验场景

注意：

- 本地 `catkin_ws` 是平级平台工作空间，不是 bringup 需要嵌入进去的目录前提。
- 后续 bringup 设计默认面向工控机上的 `~/catkin_ws` 与 `~/thesis_ws` 平级部署。

当前正式的结构规划见工作空间根目录下的 `launch/` 与 `docs/`。
