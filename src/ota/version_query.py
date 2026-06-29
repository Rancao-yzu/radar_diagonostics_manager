# -*- coding: utf-8 -*-
"""雷达软硬件版本查询模块 —— 通过 CAN 总线请求并解析版本号"""
import time
import can

# 版本查询 CAN ID 映射
VERSION_CAN_IDS = {
    'FL': {'req': 0x74F, 'resp': 0x74E},
    'FR': {'req': 0x78F, 'resp': 0x78E},
}

# 版本类型 DID
DID_SOFTWARE = 0xFF00  # 软件版本
DID_HARDWARE = 0xFF01  # 硬件版本

VERSION_TIMEOUT = 2.0  # 超时时间（秒）


def query_version(bus, radar, did, log_callback=None):
    """
    查询雷达软硬件版本号

    Args:
        bus: CAN 总线实例
        radar: 'FL' 或 'FR'
        did: DID_SOFTWARE (0xFF00) 或 DID_HARDWARE (0xFF01)
        log_callback: 日志回调函数

    Returns:
        版本号字符串（ASCII解码后），失败返回 None
    """
    ids = VERSION_CAN_IDS.get(radar)
    if ids is None:
        if log_callback:
            log_callback(f'[版本查询] 未知雷达: {radar}', 'ERROR')
        return None

    req_id = ids['req']
    resp_id = ids['resp']

    # 构造请求消息 (8 bytes)
    # Byte 1: 0x22, Byte 2-3: DID (big-endian), Byte 4-8: padding 0x00
    req_data = [0x22, (did >> 8) & 0xFF, did & 0xFF] + [0x00] * 5
    msg = can.Message(
        arbitration_id=req_id,
        data=req_data,
        is_extended_id=False,
        is_fd=True,
        dlc=len(req_data),
    )

    try:
        bus.send(msg)
        if log_callback:
            log_callback(f'[版本查询] 发送请求 {radar} DID=0x{did:04X}', 'SEND')
    except Exception as e:
        if log_callback:
            log_callback(f'[版本查询] 发送失败: {e}', 'ERROR')
        return None

    # 等待响应
    deadline = time.time() + VERSION_TIMEOUT
    while time.time() < deadline:
        remaining = deadline - time.time()
        try:
            recv = bus.recv(timeout=min(remaining, 0.1))
        except Exception as e:
            if log_callback:
                log_callback(f'[版本查询] 接收异常: {e}', 'ERROR')
            continue

        if recv is None:
            continue

        if recv.arbitration_id != resp_id:
            continue

        data = recv.data
        if len(data) < 5:
            continue

        # Byte 1: 0x62, Byte 2-3: DID, Byte 4: valid length
        if data[0] != 0x62:
            print(f'收到无效响应 {radar} DID=0x{did:04X} 数据={data.hex()}')
            continue
        resp_did = (data[1] << 8) | data[2]
        if resp_did != did:
            continue

        valid_len = data[3]
        # Byte 5+ (index 4+): ASCII version string
        ascii_bytes = bytes(data[4:4 + valid_len])
        try:
            version_str = ascii_bytes.decode('ascii')
        except UnicodeDecodeError:
            version_str = ascii_bytes.decode('ascii', errors='replace')

        if log_callback:
            log_callback(f'[版本查询] 收到响应 {radar} DID=0x{did:04X} 版本={version_str}', 'RECV')

        return version_str

    if log_callback:
        log_callback(f'[版本查询] 超时 {radar} DID=0x{did:04X}', 'ERROR')
    return None
