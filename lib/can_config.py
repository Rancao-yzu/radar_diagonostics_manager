import sys
import os
import can

def check_can_interfaces():
    """
    扫描所有可用的 Kvaser CAN 硬件接口，过滤掉虚拟设备
    返回一个列表，每个元素是一个字符串，格式为 "通道号: 设备名称 (SN: 序列号)"

    :return: 列表，包含可用的 Kvaser CAN 硬件接口信息
    """
    try:
        old_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        available_interfaces = can.detect_available_configs(interfaces=['kvaser'])
        sys.stderr.close()
        sys.stderr = old_stderr

        kvaser_interfaces = [
            cfg for cfg in available_interfaces
            if cfg['interface'] == 'kvaser' and 'Virtual' not in cfg.get('device_name', '')
        ]
        print(kvaser_interfaces)

        return [
            f"{cfg['channel']}: {cfg.get('device_name', 'Unknown')} (SN: {cfg.get('serial', 'N/A')})"
            for cfg in kvaser_interfaces
        ]

    except Exception:
        return []


def check_canoe_interfaces():
    """
    扫描 Vector CANoe 硬件接口（VN1630A 等），过滤掉虚拟通道（serial=100）
    返回一个列表，每个元素为 "0: 设备名称 (SN: 序列号)"

    :return: 列表，包含可用的 Vector/Canoe 硬件接口信息
    """
    try:
        from can.interfaces.vector import VectorBus
        configs = VectorBus._detect_available_configs()
        results = []
        for ch in configs:
            cfg = ch['vector_channel_config']
            if cfg.serial_number == 100:  # 过滤虚拟通道
                continue
            # 使用实际检测到的通道索引和设备名称
            channel = cfg.channel_index
            name = cfg.name if cfg.name else 'VN1630A'
            results.append(f"{channel}: {name} (SN: {cfg.serial_number})")
        print(results)
        return results
    except Exception:
        return []
