# tools 层

这一层用于 thesis 侧的辅助能力封装。

目标不是把工具马上实现完整，而是提前明确：

- RViz 配置应由 thesis_ws 自己管理
- rosbag 输出应写入 thesis_ws/bags
- 后续实验辅助脚本和小工具应服务于 thesis 场景，而不是修改 catkin_ws

Task1 当前使用：

- `rviz_session.launch`：正式的 thesis RViz 观察入口
- `record_session.launch`：最小 rosbag 入口，按需开启

Task2 当前也使用：

- `rviz_session.launch`：通过 thesis 入口拉起导航观察界面，当前默认引用 `rviz_navigation.rviz`
- `record_session.launch`：按需记录地图、定位、目标点与路径相关 topic

当前仍未做的事情：

- 复杂 recording 自动化
- 任务级结果自动归档
