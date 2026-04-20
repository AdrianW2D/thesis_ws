# scenarios 层

这一层是 thesis 侧真正面向实验任务的入口命名层。

约定：

- 一个展示任务，对应一个清晰的场景 launch
- 场景 launch 可以引用 `platform/` 和 `tools/`
- 场景 launch 负责表达 thesis 语义，不负责承载底层平台源码

当前预留任务：

- `task1_mapping_session.launch`：Task1 正式场景入口，当前已收口为建图展示入口
- `task2_single_goal_nav.launch`：Task2 正式场景入口，当前已收口为定位 + 单点导航入口
- `task3_patrol_stub.launch`：Task3 A1 最小多点巡检入口，当前已接入 thesis 侧 patrol manager

Task1 当前的 smoke test 启动方式：

- 当前场景 launch 位于工作空间根目录 `launch/` 下，而不是某个包内
- 因此当前推荐使用 `roslaunch $HOME/thesis_ws/launch/scenarios/task1_mapping_session.launch`
- 后续若要改成 `roslaunch <package> <file.launch>`，再把入口收口到包内

Task2 当前的 smoke test 启动方式：

- 当前推荐使用 `$HOME/thesis_ws/scripts/run_task2_active_map.sh`
- 该脚本会读取 `config/maps/map_refs.yaml` 中的 `active_map_id`，再调用正式的 Task2 场景 launch
- 若需要手工调参或切图，也可以直接调用 `roslaunch $HOME/thesis_ws/launch/scenarios/task2_single_goal_nav.launch map_id:=... map_file:=...`

Task3 A1 当前的 smoke test 启动方式：

- 当前推荐使用 `$HOME/thesis_ws/scripts/run_task3_active_map.sh`
- 该脚本会读取 `config/maps/map_refs.yaml` 中的 `active_map_id`，解析当前地图，并加载默认的 `tasks/waypoint_sets/patrol_smoke_v01.yaml`
- 若需要切换任务文件，也可以通过环境变量 `THESIS_TASK3_TASK_FILE=...` 或直接调用 `roslaunch $HOME/thesis_ws/launch/scenarios/task3_patrol_stub.launch map_id:=... map_file:=... task_file:=...`
