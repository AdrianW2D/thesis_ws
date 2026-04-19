# navigation results

这里用于沉淀 Task2 的最小结果记录。

工控机运行时，对应位置应理解为：

- `$HOME/thesis_ws/results/navigation/`

建议放入：

- 导航会话说明
- 当前活动地图与初始位姿记录
- 单点目标说明
- 全局路径 / 局部路径截图
- 到达情况与异常备注

当前阶段建议最少沉淀：

- `${session_name}.md`：本次导航说明
- `${session_name}_rviz.png`：关键界面截图
- `${session_name}_notes.txt`：临时人工备注

这里默认保留结构说明，不默认提交运行时生成的截图、摘要或临时记录。
如需长期保存关键实验结果，应另行归档，而不是直接长期堆积在 Git 仓库中。
