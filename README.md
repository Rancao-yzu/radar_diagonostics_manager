# WF Radar Diagnostics Manager

雷达诊断管理工具 —— OTA 升级 / DTC 读取清除 / 标定和标定查询

# 项目结构

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

> **注意**：必须使用 `lib/` 下的 isotp 和 uds 库，而非 pip 安装的版本。
> 程序启动时 `main.py` 会自动将 `lib/` 加入 `sys.path`。

# OTA 升级
- 提供Hex文件
- OTA 升级方案基于 PFBoot 实现客户App的升级
- 芯片上电后依次执行两级 Boot，每一级 Boot 完成自身职责后跳转到下一级，最终进入客户应用 CUAP。
- OTA 升级流程中，BM 检测到上位机发来的 FORCEJUMP 安全帧后，会停留在PFboot不再跳转到 APP，接收上位机的UDS刷写命令。


## A   进入 PFBoot OTA 模式
#### A1：扩展会话切换
- 请求 [A1] 02 10 03
- 响应 50 03 ...

#### A2：ECU复位
- 请求 [A2] 02 11 01
- 响应 51 01
  
ECU 复位中 100-200ms

#### A3：发送安全帧
- 上位机在 ECU 复位后 40ms 内开始以 1ms 周期发送安全帧, 持续 3s(建议)。
- 安全帧：专用 CAN-FD 扩展帧 ID (0x190C8532)：与日常诊断报文 ID 完全隔离, 避免误触发。  
- FORCEJUMP + 0xA5B6C7D8：重复发送，直到PFBoot识别，PFBoot 识别FORCEJUMP后, 会停留在 PFboot 状态, 等待上位机的 UDS 刷写命令。

## B  维持扩展会话
- 请求 [B1] 02 10 03
- 响应 50 03
  
每1000ms（1秒）发送一次3E 80，可以持续维持扩展会话，确保整个固件下载过程中会话不会中断。

## C  擦除目标区域
- 请求 [C] 31 01 FF 00 +0x 90 00 00
- 响应 71 01 FF 00 00

## D  下载与传输
#### D1：下载固件
- 请求 [D1] 34 00 44 + 0x90000, 2MB
- 响应 74 20 0F FA (MaxBlock = 4090)

#### D2：传输数据
- 请求 [D2] 36 SN [data...]
- 响应 76 SN

#### D3：传输结束
- 请求 [D3] 01 37 (TransferExit)
- 响应 77

## E 完整性校验与激活

#### E1：CRC32 校验
- 请求 [E1] 31 01 02 12 + CRC32
- 响应 71 01 02 12 00
  
#### E2：Dependency Check
- 请求 [E2] 31 01 02 05
- 响应 71 01 02 05 00

#### E3：Reset
- 请求 [E3] 02 11 01
- 响应 51 01
  
上位机在发送 11 01 后，停止之前周期性发送的 3E 80（在线保持）命令

