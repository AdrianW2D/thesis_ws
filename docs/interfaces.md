# thesis_ws 接口说明

本文件记录 thesis_ws 未来主要消费的接口，不把 thesis_ws 写成第二个底层驱动工作空间。

## 本地平级视图与运行时视图

- 本地平级视图：本文件中提到的 `final/catkin_ws/...` 路径用于说明本地平台基线中的接口线索来自哪里。
- 运行时视图：thesis_ws 真正部署到工控机时，应通过平级系统 `catkin_ws` 的 ROS 包、topic、tf、launch 能力工作。
- 因此，下面出现的本地路径只用于说明与核对，不构成 thesis_ws 对 catkin_ws 内部目录结构的耦合依赖。

## 主要参考来源

当前接口线索主要来自本地平级 `catkin_ws` 中的以下文件：

- `catkin_ws/src/scout_base/scout_bringup/launch/scout_minimal.launch`
- `catkin_ws/src/scout_base/scout_bringup/launch/open_rslidar.launch`
- `catkin_ws/src/scout_base/scout_bringup/launch/gmapping.launch`
- `catkin_ws/src/scout_base/scout_bringup/launch/navigation_4wd.launch`
- `catkin_ws/src/scout_base/scout_description/param/amcl_params.yaml`

## Topic 接口

| Topic | thesis 视角角色 | 上游线索 | 说明 |
| --- | --- | --- | --- |
| `/scan` | 建图/定位/导航主输入 | `open_rslidar.launch` 内部通过 `pointcloud_to_laserscan` 生成 | thesis 只消费，不重写底层激光接入链 |
| `/scan_thesis` | thesis 扫描增强前端输出 | `thesis_algorithms/scan_enhancer_node.py` | 第一条实验线中供 Task1/Task2 消费的增强扫描话题 |
| `/odom` | 里程计主输入 | `open_rslidar.launch` 中 RF2O 发布；底盘驱动链也可能参与 | thesis 视为上游能力，运行时再验证具体来源 |
| `/map` | 地图输出或静态地图输入 | `gmapping.launch` 与 `navigation_4wd.launch` | task1 用于建图输出，task2/task3 用于加载静态地图 |
| `/imu/data` | 可选姿态辅助输入 | `imu_launch` / `serial_imu` 包 | 当前不是 thesis 第一轮主线，但保留接口位 |
| `/camera/*` | 可选视觉辅助输入 | `realsense` 包 | 当前不作为主链，但接口保留 |
| `/scout_status` | 平台状态观察接口 | `scout_base/src/scout_messenger.cpp` | 可用于运行状态记录与实验摘要 |
| `/cmd_vel` | 底层速度命令边界 | `scout_messenger.cpp` 订阅 | thesis 只能在上层任务中使用，不改底盘实现 |

## TF / frame 接口

| Frame | thesis 视角角色 | 上游线索 | 说明 |
| --- | --- | --- | --- |
| `map` | 全局地图坐标系 | `gmapping.launch`、`navigation_4wd.launch` | waypoint 文件默认应以此为基准 |
| `odom` | 局部连续坐标系 | `gmapping.launch`、`amcl_params.yaml` | 作为定位/导航中间坐标系 |
| `base_footprint` | 导航底座参考系 | `gmapping.launch`、`amcl_params.yaml` | thesis 默认按该 frame 组织导航任务 |
| `base_link` | 车体主体 frame | `open_rslidar.launch`、URDF | 静态传感器外参多挂在此处 |
| `rslidar` | 激光雷达 frame | `open_rslidar.launch` 静态 TF | `/scan` 上游链的重要参考 |
| `camera_link` | 相机 frame | `open_rslidar.launch` 静态 TF | 视觉接口保留位 |
| `imu_link` | IMU frame | `open_rslidar.launch` 静态 TF | 姿态接口保留位 |

## 运行路径模型说明

为什么本地会有 `catkin_ws`：

- 为了在仓库中保留一份可阅读、可比对的平台工作空间镜像/参考基线
- 为了提炼已有包、topic、tf、launch、param 的结构信息

为什么 thesis_ws 不能依附于它的目录内部：

- thesis_ws 虽然复用 `catkin_ws` 能力，但不应把自己的运行组织写成 `catkin_ws` 内部扩展
- 运行时应依赖工控机上的平级系统 `~/catkin_ws`
- launch/config 不能写成依赖任何旧的 `reference` 路径模型

工控机上的实际关系：

```text
~/catkin_ws
~/thesis_ws
```

后续路径原则：

- launch 依赖 ROS 包解析和环境，不依赖任何旧的 `reference` 相对路径
- thesis 自己的 map/config/task 数据由 thesis_ws 管理
- 本地 `catkin_ws` 提供接口参考与平台能力，但不提供给 thesis_ws 的目录内部绑定

## 地图接口组织方式

thesis_ws 不应再把地图产物继续写回参考工作空间。建议规则如下：

- 地图引用配置文件：`config/maps/map_refs.yaml`
- thesis 自己生成的地图：`maps/generated/`
- `catkin_ws` 中已有地图：只读引用，不原地修改

这意味着：

- task1 的建图输出应落到 thesis_ws
- task2/task3 的地图选择应先查 `config/maps/map_refs.yaml`
- 当前 `active_map_id` 应作为 thesis 侧当前活动地图选择器
- Task2 当前默认活动地图为 `task1_lab_v01`
- `scripts/run_task2_active_map.sh` 会根据 `active_map_id` 解析当前运行地图

## 第一条实验线接口

第一条实验线当前采用 thesis 自己的扫描增强前端：

- 原始输入：`/scan`
- 增强输出：`/scan_thesis`
- Task1 baseline：gmapping 直接消费 `/scan`
- Task1 enhanced：gmapping 改为消费 `/scan_thesis`
- Task2 baseline：AMCL 和 move_base costmap 直接消费 `/scan`
- Task2 enhanced：AMCL 和 move_base costmap 改为消费 `/scan_thesis`

这样做的目的，是在不修改 `catkin_ws` 上游算法包的前提下，给 thesis_ws 建立一个可重复切换、可直接记录对比结果的感知前端增强位。

## 任务点接口组织方式

多点巡检当前先采用数据驱动占位，不实现执行器。

约定如下：

- 任务点文件目录：`tasks/waypoint_sets/`
- schema 说明：`config/tasks/waypoint_schema.yaml`
- 推荐文件名：`patrol_<scene>_vNN.yaml`
- 默认 frame：`map`
- 点位编号：`P01`、`P02`、`P03`

推荐字段包括：

- `point_id`
- `point_name`
- `pose.x`
- `pose.y`
- `pose.yaw`
- `task_type`
- `enabled`
- `sequence`
- `tolerance.xy`
- `tolerance.yaw_deg`
- `stay_time_sec`
- `expected_action`
- `tags`
- `note`

后续多点巡检任务可以直接读取该类文件，按 `sequence` 组织 waypoint 队列，并将到达状态、失败状态、运行备注输出到 `results/patrol/`。

## 覆盖任务接口组织方式

当前新增的 coverage 任务接口采用“两级数据组织”：

- coverage 输入配置目录：`tasks/coverage_sets/`
- coverage schema：`config/tasks/coverage_schema.yaml`
- coverage 生成器：`src/thesis_tasks/scripts/coverage_path_generator.py`
- coverage 输出 waypoint：`tasks/waypoint_sets/`

第一版 coverage 输入只支持矩形区域，推荐字段如下：

- `coverage_task_id`
- `coverage_task_name`
- `map_id`
- `frame_id`
- `area.type`
- `area.origin.x`
- `area.origin.y`
- `area.width`
- `area.height`
- `sweep.direction`
- `sweep.lane_spacing`
- `sweep.boundary_margin`
- `sweep.start_corner`
- `output.task_file`
- `output.default_task_type`

当前固定工作流为：

```text
coverage config
-> coverage_path_generator.py
-> waypoint yaml
-> task_manager_node.py
```

这样做的目的是：

- 不改底层 `move_base`
- 不让 coverage 逻辑侵入 `catkin_ws`
- 让 thesis_ws 在 Task3 上同时拥有“任务生成”和“任务执行”两层主体工作量
