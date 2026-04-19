# generated maps

Task1 生成的地图原则上应落到这个目录，而不是写回 `catkin_ws`。

工控机运行时，对应位置应理解为：

- `$HOME/thesis_ws/maps/generated/`

建议命名：

- `task1_<scene>_v01`
- `task1_<scene>_v02`
- `task1_<scene>_YYYYMMDD`

建议规则：

- 每次保存地图时同时生成 `.yaml` 与 `.pgm`
- 同一场景的地图迭代用版本号递增
- 若地图用于后续 Task2，引入前先在 `config/maps/map_refs.yaml` 中登记
