# WF Radar Diagnostics Manager

雷达诊断管理工具 —— OTA 升级 / DTC 读取清除 / 标定和标定查询 / 时间同步

# 项目结构

```
WF_Radar_Diagonostics_manager/
├── images/                # 资源文件（logo、图标等）
├── config/                # CAN 配置文件
│   ├── config_c.ini       # 标定配置
│   └── config_d.ini       # DTC 配置
├── docx/                  # 协议文档
│   ├── Calibration.md     # 标定帧结构
│   ├── DTC.md             # DTC 帧结构
│   ├── Flash.md           # 固件升级帧结构
│   ├── Ota.md             # OTA 帧结构
│   └── Time_sync.md       # 时间同步帧结构
├── lib/                   # 本地库（isotp + uds + can_config）（不可修改）
│   ├── can_config.py      # CAN 通道检测
│   ├── isotp/             # ISO-TP 协议栈
│   └── uds/               # UDS 诊断协议栈
├── src/                   # 主程序源码
│   ├── main.py            # 入口：启动 GUI，绑定事件
│   ├── gui_main.py        # GUI 主类：布局构建、功能面板
│   ├── gui_styles.py      # 主题色、自定义按钮、样式配置
│   ├── ota/               # OTA 升级模块
│   ├── dtc/               # DTC 诊断模块
│   ├── calibration/       # 标定模块
│   └── sync/              # 时间同步模块
└── src_example/           # 示例/调试脚本（不可修改）
```

> **注意**：必须使用 `lib/` 下的 isotp 和 uds 库，而非 pip 安装的版本。  
> 程序启动时 `main.py` 会自动将 `lib/` 加入 `sys.path`。  

- `src/` 为主程序源码，所有功能模块均在 `src/` 下按功能分包。
- `src_example/` 为独立示例代码，不包含在主程序中。
- `docx/` 为各模块对应的 CAN 协议文档（DBC 信号定义和帧结构说明）。

# CAN 总线架构

`main.py` 的 `Application._on_connect` 是**唯一**创建 `can.Bus` 的地方，所有功能模块共用同一个总线实例。

- `_on_connect` 负责创建 `can.Bus`（含 `can_filters`），存入 `self._bus`
- 各 Manager 的 `__init__` 接收 `bus` 参数，**不自己创建总线**
- `_on_close` 负责 `shutdown` 释放
- 若要扩展新功能模块，只需：
  1. 在 `_on_connect` 的 `filters` 中追加对应的 CAN ID
  2. 创建 Manager 时传入同一个 `self._bus` 即可


