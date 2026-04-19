# platform 层

这一层负责对接平台现有 launch 能力。

设计原则：

- 可以引用系统工作空间中已存在的上游 launch
- 不复制上游 launch 到 thesis_ws 再修改
- 只做 bridge / wrapper，不承担 thesis 结果落地

这里文件名中的 `reference_` 表示“基于本地参考分析得到的封装对象”，不是说运行时必须依赖仓库里的 `reference/` 目录。

实际运行时默认面向工控机上的平级部署：

```text
~/catkin_ws
~/thesis_ws
```

当前文件说明：

- `reference_base_bridge.launch`：底盘接入封装，Task1 中按需调用。
- `reference_sensing_bridge.launch`：激光、scan、静态 TF 等感知链接入封装。
- `reference_mapping_core.launch`：Task1 的建图核心入口，只负责 gmapping 节点，不负责 RViz/记录/结果目录。
- `reference_localization_nav_core.launch`：定位与导航核心链占位，不在第一轮直接绑定官方耦合导航 launch。

Task1 当前实际使用：

- `reference_sensing_bridge.launch`
- `reference_mapping_core.launch`
- `reference_base_bridge.launch`（可选）

Task2/Task3 当前仍保留占位：

- `reference_localization_nav_core.launch`
