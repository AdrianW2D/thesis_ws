# thesis_ws 工作约束

本文件用于约束 `thesis_ws` 内的后续开发行为，避免毕业设计主工作空间与平台参考基线混淆。

## 工作空间定位

- `thesis_ws` 是毕业设计主工作空间，不是平台基线副本。
- 本地 `catkin_ws` 是平台工作空间镜像/参考基线，与 thesis_ws 平级存在，不是 thesis 的直接编辑目标。
- thesis_ws 负责系统组织、实验流程、任务层、记录层、结果层。

## 本地平级结构与实际部署结构

本地仓库中存在：

```text
final/
├── catkin_ws
└── thesis_ws
```

这是“本地平级视图”，便于复用平台能力、对照平台已有包、launch、param、topic 和 TF。

实际部署到工控机时，应默认使用：

```text
~/catkin_ws
~/thesis_ws
```

这是“运行部署视图”。后续所有功能接入、launch 设计、config 组织和联调说明，都应默认面向这个平级部署关系。

## 必须遵守的边界

- 不修改本地 `catkin_ws` 中任何源码、launch、param、地图、rviz 配置。
- 不复制 vendor/upstream 包到 thesis_ws 再二次修改。
- 不在 thesis_ws 中重写底层驱动、CAN、传感器接入链。
- 不把 YOLO / CNN / 轻视觉检测链引入 thesis 主线。
- 不把 ROS2、底层控车重构、复杂评测自动化带入当前阶段。

## thesis_ws 内的开发原则

- 通过 launch 封装、config overlay、任务文件和记录目录复用平台能力。
- 正式实验入口放在 thesis_ws，不能直接把官方耦合 launch 当成最终 thesis 入口。
- 地图产物、任务文件、bags、logs、results 必须落在 thesis_ws 自己目录。
- 巡检语义先采用“标记点/任务点”方式表达，不以视觉识别链作为主驱动。
- 参数改动优先做 thesis overlay，不直接回写平台原始 param。
- launch 应依赖 ROS 包解析和已 source 的环境，不依赖任何 `reference` 相对路径。
- map/config/task 的运行时组织以 thesis_ws 自己目录或工控机上的系统 `catkin_ws` 包解析为准。

## Git 与运行产物边界

- thesis_ws 作为工控机上的 Git 持续更新工作空间，默认只把代码、配置、脚本、文档和 README 结构说明纳入版本管理。
- 地图、结果、bags、logs，以及 `build/`、`devel/`、`install/` 等生成物默认仅保留在本地，不作为日常提交对象。
- 根目录 `.gitignore` 必须持续维护这条边界；后续新增运行产物目录时，也应同步补充忽略规则。
- 各生成物目录中的 README 文件用于保留结构说明，不应因为目录被忽略而删除。
- 若未来误把运行产物加入 Git，应优先使用 `git rm --cached <path>` 取消跟踪并保留本地文件，再由 `.gitignore` 接管。
- 工控机日常更新流程默认是 `git pull`、重新编译、重新运行，不应把 `git clean -fdx` 之类破坏性清理命令混入常规流程。

## Task1 约束

- Task1 的正式入口为 `launch/scenarios/task1_mapping_session.launch`
- Task1 的 gmapping 核心应由 thesis 的 platform 层显式组织，而不是直接把官方 demo launch 视为最终入口
- Task1 的 RViz 观察入口应由 thesis 的 tools 层提供
- Task1 的地图应保存到 `$HOME/thesis_ws/maps/generated/`
- Task1 的结果说明与截图应归档到 `$HOME/thesis_ws/results/mapping/`
- Task1 的地图保存脚本应从 `$HOME/thesis_ws/scripts/save_task1_map.sh` 执行
- 由于 Task1 当前入口位于工作空间根目录 `launch/` 下，smoke test 阶段应使用 `roslaunch $HOME/thesis_ws/launch/scenarios/task1_mapping_session.launch` 这种文件路径调用方式
- 在未把场景 launch 收口到包内之前，不把 `roslaunch <package> <file.launch>` 当作当前 Task1 的默认启动建议
- Task1 当前只收口场景入口与结果规范，不做建图效果调优

## Task2 约束

- Task2 的正式入口为 `launch/scenarios/task2_single_goal_nav.launch`
- Task2 的定位与导航核心应由 thesis 的 platform 层显式组织，而不是直接把官方 `navigation_4wd.launch` 视为最终入口
- Task2 的地图选择应面向 `config/maps/map_refs.yaml`，当前活动地图由 `active_map_id` 指向
- Task2 当前默认导航地图为 `task1_lab_v01`
- Task2 的 smoke test 推荐通过 `$HOME/thesis_ws/scripts/run_task2_active_map.sh` 启动
- Task2 的 RViz 观察入口应由 thesis 的 tools 层提供
- Task2 的结果说明与截图应归档到 `$HOME/thesis_ws/results/navigation/`
- Task2 当前只收口场景入口、地图引用、观察入口与结果规范，不做 AMCL / DWA / move_base 深调

## 目录落位规则

- `launch/`：只放 thesis 入口和 wrapper，不放 catkin_ws 源码副本，也不写死对平台目录内部的运行依赖。
- `config/maps/`：地图引用与地图选择配置。
- `config/tasks/`：任务点 schema 与任务配置模板。
- `config/overlays/`：后续 mapping/localization/navigation overlay 放置区。
- `maps/generated/`：thesis 自己生成的地图。
- `tasks/waypoint_sets/`：多点巡检任务点集合。
- `bags/`、`logs/`、`results/`：按实验类型分区存放产物。

## 任务点约束

- 任务点文件命名推荐：`patrol_<scene>_vNN.yaml`
- 点位编号推荐：`P01`、`P02`、`P03`
- 点位名称推荐：`snake_case`
- 坐标系默认使用 `map`
- 任务文件只描述数据，不在当前阶段塞入复杂执行逻辑

## 后续构建约束

- 后续功能接入时，默认面向工控机上的 `~/catkin_ws` 与 `~/thesis_ws` 平级部署。
- 可以参考本地 `catkin_ws`，但不能把 thesis_ws 绑到 `catkin_ws` 目录内部。
- 后续若要联调，应以工控机实际目录关系、ROS 环境和包解析结果为准。
- 任何新的 launch/config/path 设计都不得要求 thesis_ws 必须放在 `final/` 下才能工作。

## 当前阶段完成口径

本阶段只做骨架，不做完整功能。允许新增目录、文档、占位配置和最小包结构；不允许借此名义改平台基线或提前实现复杂业务。
