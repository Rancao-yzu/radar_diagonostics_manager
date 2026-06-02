# -*- coding: utf-8 -*-
import struct
import time
import can

def _crc16_ccitt(data: bytes) -> int:
    """CRC-16/CCITT (poly=0x1021, init=0xFFFF)"""
    crc = 0xFFFF
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

_TSYNC_CAN_IDS = {
    "FL": 0x040,  # 前左轮
    "FR": 0x041,  # 前右轮
    "RL": 0x042,  # 后左轮
    "RR": 0x043,  # 后右轮
}

class TimeSyncManager:
    """时间同步管理器 — 打包 CANFD 扩展帧并通过共享总线发送"""

    def __init__(self, bus: can.BusABC, log_callback=None):
        self.bus = bus
        self.log_callback = log_callback
        self._seq_counter = 0

    def _log(self, msg, tag="INFO"):
        print(msg)
        if self.log_callback:
            self.log_callback(msg, tag)

    def build_and_send(self, msg_type=0x20):
        """取当前系统时间，按协议打包 64 字节 CANFD 扩展帧，向四轮 CAN ID 各发一帧"""
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 1e9)

        raw = bytearray(64)

        # Byte2~5 — TSYNC_GT_Nanoseconds（4 字节，大端序 u32）
        struct.pack_into('>I', raw, 2, nanos)

        # Byte6~9 — TSYNC_GT_Seconds（4 字节，大端序 u32）
        struct.pack_into('>I', raw, 6, seconds)

        # Byte10  — TSYNC_message_type（1 字节，u8），消息类型
        raw[10] = msg_type

        # Byte11  — TSYNC_SequenceCounter（1 字节，u8），每发一帧自增，0~255 循环
        raw[11] = self._seq_counter

        # Byte12~14 — TSYNC_Reserved（3 字节，u24），协议保留位，填充 0x00
        raw[12:15] = b'\x00' * 3

        # Byte15  — TSYNC_Status（1 字节，u8），设备状态字，当前固定 0x00
        raw[15] = 0x00

        # Byte16~63 — 未使用，填充 0x00
        raw[16:64] = b'\x00' * 48

        # Byte0~1 — TSYNC_CRC（2 字节，大端序 u16）
        # CRC 校验范围：Byte2~Byte63（除 CRC 字段外的其它有效数据）
        crc = _crc16_ccitt(bytes(raw[2:64]))
        struct.pack_into('>H', raw, 0, crc)

        self._log(f"[SYNC] 发送时间同步帧 seq={self._seq_counter} "
                  f"s={seconds} ns={nanos} crc=0x{crc:04X}", "SEND")

        # 向四轮 CAN ID 各发送一帧
        for wheel, can_id in _TSYNC_CAN_IDS.items():
            msg = can.Message(
                arbitration_id=can_id,
                data=bytes(raw),
                is_extended_id=True,
                is_fd=True,
                dlc=64,
            )
            self.bus.send(msg)

        # 序列号递增，0~255 循环
        self._seq_counter = (self._seq_counter + 1) & 0xFF

        # 帧末尾输出空行，利于 GUI 日志阅读
        self._log("", "INFO")
