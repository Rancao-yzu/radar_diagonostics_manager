#!/usr/bin/env python3
# canfd_receive_ch1.py - 通道1持续接收

import can
from can.interfaces.vector import VectorBus

# 自动检测序列号
channels = VectorBus._detect_available_configs()
SERIAL = None
for ch in channels:
    config = ch['vector_channel_config']
    if config.serial_number != 100:  # 过滤虚拟通道
        SERIAL = config.serial_number
        print(f"SN={SERIAL}")
        break

if SERIAL is None:
    print("错误: 未找到 VN1630A 设备")
    exit(1)

with VectorBus(
    channel=0,
    serial=SERIAL,
    bitrate=500000,
    data_bitrate=2000000,
    fd=True,
    app_name=None
) as bus:
    print("通道 1 (CH1/3) 已连接，开始接收消息...")
    print("按 Ctrl+C 停止接收\n")
    
    count = 0
    try:
        while True:
            msg = bus.recv(timeout=1.0)
            if msg:
                count += 1
                fd_flag = "FD" if msg.is_fd else "Classic"
                print(f"[{count}] 收到 {fd_flag} 消息:")
                print(f"    ID: 0x{msg.arbitration_id:08x}")
                print(f"    DLC: {msg.dlc}")
                print(f"    数据: {msg.data.hex()}")
                if msg.is_fd and msg.bitrate_switch:
                    print("    比特率切换: 已启用")
                print()
                
    except KeyboardInterrupt:
        print(f"\n停止接收，共收到 {count} 条消息")