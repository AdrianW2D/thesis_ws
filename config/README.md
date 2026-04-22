# config 分层规则

`config/` 只组织 thesis 侧配置，不直接改平台原始 param。

当前分层如下：

- `maps/`：地图引用配置，解决“用哪张图”的问题
- `tasks/`：任务点 schema 和任务文件约束
- `experiments/`：实验 profile，解决“这次实验记录什么、输出到哪里”的问题
- `overlays/`：后续参数 overlay 放置区，解决“在不改平台原 param 的前提下做 thesis 封装”的问题

当前 overlay 已开始细分到具体实验线：

- `overlays/mapping/`：Task1 建图核心参数
- `overlays/sensing/`：thesis 自己的感知前端增强参数
- `overlays/navigation/`：后续导航增强参数预留

核心原则：

- 不直接修改本地 `catkin_ws` 的 param
- thesis 只做 overlay 或封装
- 地图、任务点、实验记录都以 thesis 目录为归宿
- 本地配置中的仓库相对路径字段只用于分析和索引，不应作为工控机运行时路径契约
- 运行时路径应面向 thesis_ws 自己目录和工控机环境中的系统 `catkin_ws`
