import can
import sys
import os

def check_can_interfaces_once():
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

        print("检测到的 Kvaser 硬件接口：")
        for idx, cfg in enumerate(kvaser_interfaces, 1):
            print(f"  {idx}. 通道 {cfg['channel']}: {cfg['device_name']} -SN 0{cfg['serial']}")
        print()

        return kvaser_interfaces
        
    except Exception as e:
        print(f"检测CAN接口错误: {e}")
        return []
        
check_can_interfaces_once()
