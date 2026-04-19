# scenarios 层

这一层是 thesis 侧真正面向实验任务的入口命名层。

约定：

- 一个展示任务，对应一个清晰的场景 launch
- 场景 launch 可以引用 `platform/` 和 `tools/`
- 场景 launch 负责表达 thesis 语义，不负责承载底层平台源码

当前预留任务：

- `task1_mapping_session.launch`：Task1 正式场景入口，当前已收口为建图展示入口
- `task2_single_goal_nav.launch`
- `task3_patrol_stub.launch`

Task1 当前的 smoke test 启动方式：

- 当前场景 launch 位于工作空间根目录 `launch/` 下，而不是某个包内
- 因此当前推荐使用 `roslaunch $HOME/thesis_ws/launch/scenarios/task1_mapping_session.launch`
- 后续若要改成 `roslaunch <package> <file.launch>`，再把入口收口到包内
