# WF Radar Diagnostics Manager

雷达诊断管理工具 —— OTA 升级 / DTC 读取清除 / 标定和标定查询

## 概述

基于 Python/Tkinter 的桌面应用程序，通过 CAN 总线与雷达设备通信，提供以下功能：

- **OTA 升级**：通过 UDS 协议远程升级雷达固件
- **DTC 读取/清除**：读取/清除雷达故障码
- **标定和标定查询**：雷达参数标定与查询

> 当前版本中，三个功能面板均为占位状态，界面框架已就绪。

## 界面预览

- 扁平化设计，白色/浅蓝主题
- 上下布局：上为操作区域，下为通讯日志
- 左侧功能选择栏，三个导航按钮互斥切换
- CAN 总线配置区：Channel、Bitrate、Data Bitrate

## 快速开始

```bash
pip install python-can
python src/main.py
```

## 项目结构

```
├── images/              # 资源文件
├── lib/                 # 本地库（isotp + uds）
├── src/                 # 主程序源码
│   ├── main.py          # 程序入口
│   ├── gui_main.py      # GUI 主类（布局 + 面板）
│   ├── gui_styles.py    # 主题色 + 自定义组件
│   └── can_config.py    # CAN 通道检测
└── src_example/         # 示例脚本
```

## 更多

构建与安装说明详见 [build.md](build.md)。
