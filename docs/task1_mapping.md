# Task1: 地图构建与系统感知链展示

## 目标

Task1 的目标不是优化建图算法，而是让 thesis_ws 正式接管“建图展示会话”的系统组织。

本任务由 thesis_ws 负责：

- 组织场景入口
- 组织 RViz 观察入口
- 规范地图输出位置
- 规范结果归档位置

本任务由 catkin_ws 负责：

- 提供底盘、激光、scan、tf 等底层能力
- 提供平台已有的感知接入链

## 正式入口

Task1 的正式场景入口为：

- `thesis_ws/launch/scenarios/task1_mapping_session.launch`

它负责组合三层内容：

- `platform/`：平台能力接入与建图核心
- `tools/`：RViz 与最小 rosbag 入口
- `scenarios/`：Task1 的场景编排与参数选择

第一条实验线已在 Task1 中预留了扫描增强前端接入位：

- 关闭增强时，建图核心直接消费 `/scan`
- 开启增强时，Task1 会先启动 `launch/platform/thesis_scan_frontend.launch`，再让 gmapping 消费 `/scan_thesis`

## 三层关系

### platform 层

Task1 当前调用：

- `launch/platform/reference_sensing_bridge.launch`
- `launch/platform/reference_base_bridge.launch`（按需开启）
- `launch/platform/reference_mapping_core.launch`
- `launch/platform/thesis_scan_frontend.launch`（第一条实验线中按需开启）

其中：

- `reference_sensing_bridge.launch`：接入激光/scan/TF 等基础链
- `reference_base_bridge.launch`：按需接入底盘
- `reference_mapping_core.launch`：只负责 gmapping 节点，不负责 RViz 和结果归档
- `thesis_scan_frontend.launch`：thesis 自己的扫描增强前端，用于 baseline/enhanced 对比

### tools 层

Task1 当前调用：

- `launch/tools/rviz_session.launch`
- `launch/tools/record_session.launch`（按需开启）

其中：

- `rviz_session.launch`：Task1 的 thesis 观察入口
- `record_session.launch`：最小 rosbag 入口

### scenarios 层

- `task1_mapping_session.launch` 是 Task1 的正式入口
- 它负责编排 platform + tools，而不是把所有逻辑塞进一个 launch

## 地图输出规范

Task1 地图原则上应保存到：

- `$HOME/thesis_ws/maps/generated/`

推荐命名：

- `task1_lab_v01`
- `task1_hallway_v01`
- `task1_roomA_YYYYMMDD`

建议：

- 地图命名体现任务、场景、版本
- 用 `$HOME/thesis_ws/scripts/save_task1_map.sh` 保存地图
- 后续若 Task2 要使用该地图，应在 `config/maps/map_refs.yaml` 中登记

## 结果归档规范

Task1 结果原则上应归档到：

- `$HOME/thesis_ws/results/mapping/`

建议归档内容：

- 建图说明 Markdown
- RViz 截图
- 地图版本记录
- 环境与异常备注

## 最小运行建议

建议流程：

1. source ROS Melodic 基础环境
2. source 平台工作空间环境
3. 再 source thesis_ws 的 overlay 环境
4. 从 thesis 侧启动 Task1 场景入口
5. 建图结束后，用 thesis 脚本保存地图到 `maps/generated/`
6. 将截图和说明写入 `results/mapping/`

当前更符合实际的启动口径是：

- 由于 `task1_mapping_session.launch` 当前位于 `$HOME/thesis_ws/launch/scenarios/`，而不是某个 ROS 包的 `launch/` 目录中，所以当前 smoke test 应使用 `roslaunch` 直接指向 launch 文件路径
- 这属于 ROS1 允许的文件路径启动方式，适合当前结构
- 后续如果要完全收口到标准包内启动习惯，再把该场景入口下沉到 `thesis_bringup/launch/`

示例命令结构：

```bash
source /opt/ros/melodic/setup.bash
source "$HOME/catkin_ws/devel/setup.bash"
source "$HOME/thesis_ws/devel/setup.bash"
roslaunch "$HOME/thesis_ws/launch/scenarios/task1_mapping_session.launch"
```

第一条实验线建议使用：

```bash
"$HOME/thesis_ws/scripts/init_line1_scan_frontend_record.sh" exp_line1_lab_v01
"$HOME/thesis_ws/scripts/run_task1_scan_frontend_experiment.sh" baseline exp_line1_task1_baseline
"$HOME/thesis_ws/scripts/run_task1_scan_frontend_experiment.sh" enhanced exp_line1_task1_enhanced
```

地图保存建议：

```bash
"$HOME/thesis_ws/scripts/save_task1_map.sh" task1_lab_v01
```

当前阶段的最小验证标准：

- thesis 入口能拉起 Task1 场景
- 激光/TF/建图链可在 RViz 中观察
- 地图可保存到 `$HOME/thesis_ws/maps/generated/`
- 结果可记录到 `$HOME/thesis_ws/results/mapping/`
