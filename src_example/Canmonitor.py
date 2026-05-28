#!/usr/bin/env python3
import can
import sys

try:
    with can.Bus(
        interface="kvaser",
        channel=1,
        bitrate=500000,
        fd=True,
        data_bitrate=2000000,
    ) as bus:
        while True:
            msg = bus.recv(timeout=1.0)
            if msg is not None:
                data_hex = " ".join(f"{b:02X}" for b in msg.data)
                id_type = "EXT" if msg.is_extended_id else "STD"
                fd_str = ",FD" if msg.is_fd else ""
                print(f"ID=0x{msg.arbitration_id:X}({id_type}{fd_str})  DLC={msg.dlc}  数据=[{data_hex}]")

                '''
                OUT:
                ID=0x41(STD,FD)  DLC=8  数据=[00 00 00 00 00 00 00 00]
                ID=0x41(EXT,FD)  DLC=12  数据=[00 00 00 00 00 00 00 00 00 00 00 00]
                '''

except can.CanError as e:
    print(f"CAN 错误: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"错误: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    print("\n监听已停止")
