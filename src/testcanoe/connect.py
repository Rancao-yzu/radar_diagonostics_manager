#!/usr/bin/env python3
# send_fd_10times.py - CAN FD 发送10次

import can
import time
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
    print("通道 1 (CH1/3) 已连接 (CAN FD)")
    print("仲裁段: 500k, 数据段: 2M")

    
    for i in range(10):
        msg = can.Message(
            arbitration_id=0x01,
            data=[i, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07],
            is_extended_id=False,
            is_fd=True,
            bitrate_switch=False,
            dlc=8
        )
        
        bus.send(msg)
        print(f"[{i+1}] 发送: ID=0x{msg.arbitration_id:08x} DLC={msg.dlc} Data={msg.data.hex()}")
        time.sleep(0.1)
    
    print("\n发送完成")