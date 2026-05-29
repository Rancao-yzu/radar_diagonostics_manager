# WF Radar Diagnostics Manager

雷达诊断管理工具 —— OTA 升级 / DTC 读取清除 / 标定和标定查询

# 项目结构

```
WF_Radar_Diagonostics_manager/
├── images/              # 资源文件（logo 等）
├── lib/                 # 本地库（isotp + uds）（不可修改）
   └── can_config.py    # CAN 通道检测
├── src/                 # 主程序源码
├── ota/                 # OTA 升级相关代码
├── calibration/         # calibration相关代码
│   ├── main.py          # 入口：启动 GUI，绑定事件
│   ├── gui_main.py      # GUI 主类：布局构建、功能面板
│   ├── gui_styles.py    # 主题色、自定义按钮、样式配置
└── src_example/         # 示例/调试脚本（不可修改）
```

> **注意**：必须使用 `lib/` 下的 isotp 和 uds 库，而非 pip 安装的版本。  
> 程序启动时 `main.py` 会自动将 `lib/` 加入 `sys.path`。  
> 已完成src/ota/ota_test.py，用于测试 OTA 升级流程！  

- 其中src/ota/ota_test.py为单独的ota测试程序，不侵入主程序。
- src_example/为示例代码，不包含在主程序中。
- src/为主程序源码，包含所有功能模块。
