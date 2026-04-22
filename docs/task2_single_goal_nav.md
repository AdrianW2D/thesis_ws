# Task2: 定位 + 单点导航

## 目标

Task2 的目标不是优化导航参数，而是让 thesis_ws 正式接管“地图加载 + 定位 + 单点导航”实验会话的组织。

本任务由 thesis_ws 负责：

- 组织正式场景入口
- 通过 thesis 的地图索引选择当前活动地图
- 组织 RViz 观察入口
- 规范结果归档位置

本任务由 catkin_ws 负责：

- 提供底盘、激光、TF 与上游导航栈依赖包
- 提供上游 AMCL 与 move_base 参数文件

## 正式入口

Task2 的正式场景入口为：

- `thesis_ws/launch/scenarios/task2_single_goal_nav.launch`

它负责组合三层内容：

- `platform/`：平台能力接入、map_server、AMCL、move_base
- `tools/`：RViz 与最小 rosbag 入口
- `scenarios/`：Task2 场景编排与参数选择

当前推荐的 smoke test 启动脚本为：

- `$HOME/thesis_ws/scripts/run_task2_active_map.sh`

第一条实验线在 Task2 中额外提供：

- `$HOME/thesis_ws/scripts/run_task2_scan_frontend_experiment.sh`

这个脚本会从 `config/maps/map_refs.yaml` 读取 `active_map_id`，解析当前活动地图，再调用正式的 Task2 场景 launch。

## 三层关系

### platform 层

Task2 当前调用：

- `launch/platform/reference_base_bridge.launch`
- `launch/platform/reference_sensing_bridge.launch`
- `launch/platform/reference_localization_nav_core.launch`
- `launch/platform/thesis_scan_frontend.launch`（第一条实验线中按需开启）

其中：

- `reference_base_bridge.launch`：接入底盘基础链
- `reference_sensing_bridge.launch`：接入激光、scan、TF 等基础链
- `reference_localization_nav_core.launch`：只负责 `map_server + amcl + move_base`
- `thesis_scan_frontend.launch`：thesis 的扫描增强前端。开启时，AMCL 与 costmap 改为消费 `/scan_thesis`

### tools 层

Task2 当前调用：

- `launch/tools/rviz_session.launch`
- `launch/tools/record_session.launch`（按需开启）

其中：

- `rviz_session.launch`：Task2 的 thesis 观察入口
- `record_session.launch`：最小 rosbag 入口

### scenarios 层

- `task2_single_goal_nav.launch` 是 Task2 的正式入口
- 它负责编排 platform + tools，而不是直接把官方耦合导航 demo 当 thesis 最终入口

## 当前地图引用方式

Task2 当前通过 thesis 的地图索引进入运行流程：

- 地图索引文件：`config/maps/map_refs.yaml`
- 当前活动地图键：`active_map_id`
- 当前默认活动地图：`task1_lab_v01`

当前约定是：

- `task1_lab_v01` 对应 Task1 已生成并登记的 thesis 自有地图
- `run_task2_active_map.sh` 会从 `active_map_id` 解析出当前地图文件
- `task2_single_goal_nav.launch` 接收 `map_id` 与 `map_file` 两个显式参数

这意味着 Task2 不再把手写固定地图路径当成唯一入口，而是面向 thesis 的地图索引机制组织。

## RViz 观察入口

Task2 当前默认使用 thesis tools 层提供的 RViz 入口：

- `launch/tools/rviz_session.launch`

当前默认配置引用：

- `$(find scout_description)/rviz/rviz_navigation.rviz`

这仍然复用了上游 RViz 配置思路，但启动 ownership 已经放回 thesis_ws。

## 结果归档规范

Task2 结果原则上应归档到：

- `$HOME/thesis_ws/results/navigation/`

当前阶段建议最少沉淀：

- 本次实验说明 Markdown
- 初始位姿与目标点记录
- 全局路径 / 局部路径截图说明
- 导航是否到达与异常备注

## 最小 smoke test 建议

建议流程：

1. source ROS Melodic 基础环境
2. source 平台工作空间环境
3. source thesis_ws 的 overlay 环境
4. 使用 thesis 的 active map 启动脚本拉起 Task2
5. 在 RViz 中确认地图、激光、机器人位姿与 AMCL 粒子
6. 在 RViz 中发送单点目标并观察导航链是否成立

示例命令结构：

```bash
source /opt/ros/melodic/setup.bash
source "$HOME/catkin_ws/devel/setup.bash"
source "$HOME/thesis_ws/devel/setup.bash"
"$HOME/thesis_ws/scripts/run_task2_active_map.sh"
```

第一条实验线建议使用：

```bash
"$HOME/thesis_ws/scripts/run_task2_scan_frontend_experiment.sh" baseline exp_line1_task2_baseline
"$HOME/thesis_ws/scripts/run_task2_scan_frontend_experiment.sh" enhanced exp_line1_task2_enhanced
```

如需同时录包：

```bash
"$HOME/thesis_ws/scripts/run_task2_active_map.sh" record_bag:=true
```

最小验证要点：

- 地图正确加载，`/map` 有内容
- RViz 中可见地图、激光、机器人位姿和 AMCL 粒子
- 发送 `2D Nav Goal` 后可见全局路径和局部路径
- 机器人能开始响应导航目标，`/move_base/status` 有状态变化

当前阶段的最小成功判据：

- thesis 入口能拉起 Task2 场景
- 当前活动地图来自 `config/maps/map_refs.yaml`
- RViz 中定位链成立
- 单点导航链成立
- 结果目录已经明确为 `$HOME/thesis_ws/results/navigation/`
