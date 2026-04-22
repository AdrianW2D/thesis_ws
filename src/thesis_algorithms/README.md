# thesis_algorithms

该包用于放置 thesis 自己拥有的算法增强节点。

当前已落地：

- `scan_enhancer_node.py`：第一条实验线的扫描增强前端。输入原始 `/scan`，输出 thesis 自己管理的增强扫描话题，供 Task1/Task2 做 baseline/enhanced 对比。

设计边界：

- 不修改 `catkin_ws` 中的上游算法包
- 通过 thesis 自己的节点和 launch 接入 Task1 / Task2 / Task3
- 算法参数由 `config/overlays/` 管理，而不是改上游 param
