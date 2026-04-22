# sensing overlays

这里放 thesis 自己的感知前端增强参数，不直接修改平台原始参数。

当前已定义：

- `scan_enhancer_baseline.yaml`：第一条实验线的 baseline 参数，占位为“基本直通”，便于统一入口和统一记录
- `scan_enhancer_enhanced.yaml`：第一条实验线的 enhanced 参数，启用 thesis 扫描增强前端

第一条实验线的目标不是替换上游建图/导航算法，而是在 thesis_ws 内增加一个可切换、可对比的感知前端层。
