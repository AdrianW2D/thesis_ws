# thesis_ws 第一轮系统骨架

`thesis_ws` 是毕业设计“清扫机器人智能巡检系统设计与实现”的主工作空间。
它不是第二个底层驱动工作空间，而是上层实验系统、任务组织层、记录层和结果沉淀层。

## 本地参考结构与实际部署结构

当前本地仓库中存在如下结构：

```text
final/
├── catkin_ws/
└── thesis_ws/
```

这里的 `catkin_ws` 是本地官方平台工作空间镜像/参考基线，同时也作为 thesis_ws 在本地联调时的平级平台工作空间。

工控机上的实际部署视图应理解为：

```text
~/catkin_ws   # 工控机上的系统官方工作空间
~/thesis_ws   # 工控机上的毕业设计工作空间
```

现在本地与工控机都采用“平级工作空间模型”。后续 thesis_ws 的 launch、config、map、task 组织都必须面向这种平级关系，而不是依赖任何 `reference/` 路径假设。

## 角色边界

- 本地 `catkin_ws`：平台工作空间镜像/参考基线，负责提供底层能力、结构参考、接口线索和上游 launch/param 对照。
- `thesis_ws`：毕业设计主工作空间，负责 thesis 侧系统入口、实验流程、任务点组织、记录输出、评测沉淀与文档约束。

本工作空间在第一轮只完成骨架搭建，不做以下事情：

- 默认不修改本地 `catkin_ws`
- 不复制上游 vendor 包到 thesis_ws 改造
- 不实现完整巡检算法
- 不引入 YOLO / CNN / 轻视觉检测主链
- 不做导航深调和平台级重构

## 当前目录职责

- `src/`：thesis 侧最小 ROS 包边界，占位后续 bringup、任务层、记录层代码。
- `launch/`：thesis 侧 launch 分层与正式入口命名。
- `config/`：地图引用、任务点 schema、实验 profile、参数 overlay 约束。
- `rviz/`：thesis 自己拥有的 RViz 配置放置区，避免直接改参考配置。
- `bags/`：按任务分类保存 rosbag。
- `logs/`：运行日志与手工记录摘要。
- `results/`：建图、导航、巡检的结果产物与摘要。
- `docs/`：架构、接口与工作空间约束说明。
- `maps/`：thesis 侧地图产物放置区，不反写 catkin_ws 地图目录。
- `tasks/`：任务点集合和巡检任务定义文件。
- `scripts/`：后续用于实验辅助的小脚本，不放底层业务逻辑。

上面的目录职责面向 `thesis_ws` 自身成立，不要求 thesis_ws 必须位于 `final/` 下才能工作。

## 第一轮最小模块

- `thesis_bringup`：系统启动封装层。未来负责 thesis 正式入口与平台能力接入。
- `thesis_tasks`：任务点配置层。未来负责 waypoint/巡检任务装载与执行编排。
- `thesis_recording`：实验记录层。未来负责 rosbag、日志、结果摘要与简单评测沉淀。

当前这三个包只建立边界，不实现完整节点逻辑。

## 面向后续三任务的承接关系

- 任务 1 建图展示：使用 `launch/scenarios/task1_mapping_session.launch`、`config/experiments/profiles.yaml`、`maps/generated/`、`results/mapping/`
- 任务 2 单点导航：使用 `launch/scenarios/task2_single_goal_nav.launch`、`config/maps/map_refs.yaml`、`results/navigation/`
- 任务 3 多点巡检雏形：使用 `launch/scenarios/task3_patrol_stub.launch`、`tasks/waypoint_sets/`、`config/tasks/waypoint_schema.yaml`、`results/patrol/`

## Task1 正式入口

Task1 现在不再只是结构占位。thesis_ws 已将“地图构建与系统感知链展示”收口为正式场景入口：

- 场景入口：`launch/scenarios/task1_mapping_session.launch`
- 建图核心：`launch/platform/reference_mapping_core.launch`
- RViz 入口：`launch/tools/rviz_session.launch`
- 地图输出目录：`maps/generated/`
- 结果归档目录：`results/mapping/`
- 地图保存脚本：`scripts/save_task1_map.sh`

Task1 中的职责划分如下：

- `catkin_ws`：提供底层平台能力与已有感知接入链
- `thesis_ws`：组织建图场景、观察入口、地图输出规范与结果沉淀规范

Task1 的工控机运行口径如下：

- 地图输出位置：`$HOME/thesis_ws/maps/generated/`
- 结果归档位置：`$HOME/thesis_ws/results/mapping/`
- 地图保存脚本：`$HOME/thesis_ws/scripts/save_task1_map.sh`

当前 Task1 的正式入口位于工作空间根目录 `launch/` 下，而不是某个 ROS 包内。
因此本轮 smoke test 的推荐方式是使用 `roslaunch` 直接指向 launch 文件路径，而不是写成 `roslaunch <package> <file.launch>`。
后续若需要完全收口到包内入口，再将场景 launch 下沉到 `thesis_bringup/launch/`。

更完整的 Task1 说明见：

- `docs/task1_mapping.md`

## Task2 正式入口

Task2 当前已将“定位 + 单点导航”收口为 thesis 的正式场景入口：

- 场景入口：`launch/scenarios/task2_single_goal_nav.launch`
- 定位导航核心：`launch/platform/reference_localization_nav_core.launch`
- 地图索引：`config/maps/map_refs.yaml`
- 活动地图启动脚本：`scripts/run_task2_active_map.sh`
- RViz 入口：`launch/tools/rviz_session.launch`
- 结果归档目录：`results/navigation/`

Task2 中的职责划分如下：

- `catkin_ws`：提供底层平台能力、AMCL 参数文件、move_base 参数文件与导航栈依赖
- `thesis_ws`：组织活动地图选择、定位导航场景、观察入口与结果归档规范

Task2 当前的地图引用方式如下：

- `config/maps/map_refs.yaml` 是 thesis 层地图索引
- `active_map_id` 当前设为 `task1_lab_v01`
- `scripts/run_task2_active_map.sh` 会根据 `active_map_id` 解析当前地图，并调用正式的 Task2 场景 launch

更完整的 Task2 说明见：

- `docs/task2_single_goal_nav.md`

## 本地平级视图与运行时视图

- 本地平级视图：`final/catkin_ws` 与 `final/thesis_ws` 平级存在，便于在本地复用平台能力、核对接口和组织 thesis 侧入口。
- 运行时部署视图：thesis_ws 在工控机上与系统 `catkin_ws` 也保持平级，通过 ROS 包解析、topic、tf 和 launch 机制接入，而不是依附于 `catkin_ws` 目录内部。
- thesis_ws 通过 wrapper launch、overlay config、任务文件与结果目录复用平台能力。
- thesis_ws 不直接把官方耦合 launch 视为毕业设计正式入口，也不把任何旧的 `reference/` 路径视为运行前提。

## 路径原则

- launch 应依赖 ROS 包解析和已 source 的环境，不依赖任何 `reference` 相对路径。
- map、config、task、bag、log、result 数据由 thesis_ws 自己管理。
- 本地 `catkin_ws` 提供平级平台能力与结构参考，但不提供给 thesis_ws 的目录内部耦合前提。
- 后续联调与部署默认面向工控机上的 `~/catkin_ws` 与 `~/thesis_ws` 平级结构。

## Git 更新与运行产物隔离

`thesis_ws` 后续会作为工控机上通过 Git 持续更新的主工作空间使用，因此需要明确区分两类内容：

- 受 Git 管理的内容：代码、launch、config、docs、scripts、tasks，以及各目录中的 README 结构说明文件
- 默认仅本地保留的内容：地图、结果、bags、logs，以及 `build/`、`devel/`、`install/` 等运行和编译生成物

当前根目录 `.gitignore` 已按这个原则配置，目标是：

- `git pull` 只更新 thesis_ws 的代码与配置
- `maps/generated/`、`results/`、`bags/`、`logs/` 中的本地实验资产默认不纳入版本控制
- 目录中的 README 文件继续保留，用于说明结构用途和建议落位

工控机后续推荐更新流程：

1. 进入 `$HOME/thesis_ws`
2. 执行 `git pull`
3. 重新编译 thesis_ws
4. 再运行实验

只要运行产物未被 Git 跟踪且被 `.gitignore` 排除，普通 `git pull` 不应主动影响这些本地文件。
需要注意的是，`git clean -fdx` 这类显式清理命令仍会删除被忽略的本地生成物，因此不应把它当作日常更新步骤。

若需长期保存关键实验结果，应另行归档，而不是默认提交回仓库。

## 第一轮完成标准

满足以下条件即可视为“第一轮骨架构建完成”：

- `thesis_ws/` 已存在并具备顶层目录骨架
- `src/` 下已存在最小模块边界和 catkin 入口占位
- `launch/`、`config/`、`tasks/` 已形成可继续扩展的命名和分层规则
- `README.md`、`AGENT.md`、`docs/architecture.md`、`docs/interfaces.md` 已写明边界与接口
- 建图、单点导航、多点巡检三类任务均已有独立的结构承接位置
- 所有地图、bag、日志、结果产物都明确落在 thesis_ws 自己目录中
- 本地 `catkin_ws` 未被改动
