# overlay 规则

这一层专门为 thesis 的后续参数覆盖预留，不允许直接改 reference 原始参数文件。

建议原则：

- mapping 相关覆盖放到 `mapping/`
- localization 相关覆盖放到 `localization/`
- navigation 相关覆盖放到 `navigation/`

overlay 的用途是：

- 保持平台原始参数只读
- 让论文实验参数变化有自己的记录位置
- 便于对不同实验 profile 做最小差异管理
