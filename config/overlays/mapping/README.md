# mapping overlays

未来用于放置 thesis 侧的建图参数覆盖文件。

约束：

- 不直接修改上游 `gmapping.launch` 或其原始参数来源
- 只在 thesis 场景入口中以 overlay 方式加载

当前已提供：

- `gmapping_task1.yaml`：Task1 建图场景使用的最小 gmapping 参数文件
