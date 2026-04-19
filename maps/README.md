# maps

这里用于保存 thesis 侧地图资产。

规则：

- `generated/` 保存 thesis 自己生成的地图
- `catkin_ws` 中已有地图只能作为只读参考，不在原目录回写
- 地图选择优先通过 `config/maps/map_refs.yaml` 统一管理

Task1 当前默认把地图保存到：

- `maps/generated/`

建议优先使用 thesis 层脚本保存地图，而不是手工保存到 `catkin_ws`。
