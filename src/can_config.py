import sys
import os
import can

def check_can_interfaces():
    """扫描所有可用的 Kvaser CAN 硬件接口，过滤掉虚拟设备"""
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
