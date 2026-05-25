# 构建

# 运行程序
python src/main.py
```

## 项目结构

```
WF_Radar_Diagonostics_manager/
├── images/              # 资源文件（logo 等）
├── lib/                 # 本地库（isotp + uds）（不可修改）
├── src/                 # 主程序源码
│   ├── main.py          # 入口：启动 GUI，绑定事件
│   ├── gui_main.py      # GUI 主类：布局构建、功能面板
│   ├── gui_styles.py    # 主题色、自定义按钮、样式配置
│   └── can_config.py    # CAN 通道检测
└── src_example/         # 示例/调试脚本（不可修改）
```

## 文件说明

| 文件 | 职责 |
|------|------|
| `main.py` | 程序入口，创建窗口、绑定按钮事件、管理生命周期 |
| `gui_main.py` | `RadarDiagnosticsGUI` 类，构建主布局/侧栏/CAN配置/功能面板/日志区 |
| `gui_styles.py` | 主题色常量、`_FlatButton`/`_SideButton` 自定义组件、ttk 样式配置 |
| `can_config.py` | 调用 `src_example/list_can.py` 获取可用 CAN 通道列表 |

## 界面架构

- 上下布局：上为操作区域，下为日志区域
- 操作区域左右分割：左侧功能选择栏（三个导航按钮），右侧为当前选中功能的面板
- 三个功能面板均为占位状态：OTA 升级、DTC 读取/清除、标定和标定查询

> **注意**：必须使用 `lib/` 下的 isotp 和 uds 库，而非 pip 安装的版本。
> 程序启动时 `main.py` 会自动将 `lib/` 加入 `sys.path`。
