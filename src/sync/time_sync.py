# -*- coding: utf-8 -*-
import struct
import time

import can

# CANFD 扩展帧 0x0400，16 字节
# 字段布局（大端序）：
#   Byte0      — 消息类型         u8
#   Byte1~2    — CRC-16 校验码    u16
#   Byte3      — 帧序列号         u8
#   Byte4      — 设备状态字       u8
#   Byte5~8    — 全局时间秒       u32
#   Byte9~12   — 全局时间纳秒     u32
#   Byte13~15  — 协议保留位


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
        """取当前系统时间，按协议打包 16 字节 CANFD 扩展帧并通过共享总线发送"""
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 1e9)

        raw = bytearray(16)

        # Byte0   — 消息类型（1 字节，u8），固定 0x20
        raw[0] = msg_type

        # Byte3   — 帧序列号（1 字节，u8），每发一帧自增，0~255 循环
        raw[3] = self._seq_counter

        # Byte4   — 设备状态字（1 字节，u8），当前固定 0x00
        raw[4] = 0x00

        # Byte5~8 — 全局时间秒（4 字节，大端序 u32）
        struct.pack_into('>I', raw, 5, seconds)

        # Byte9~12 — 全局时间纳秒（4 字节，大端序 u32）
        struct.pack_into('>I', raw, 9, nanos)

        # Byte13~15 — 协议保留位（3 字节，填充 0x00）
        raw[13:16] = b'\x00' * 3

        # 计算 CRC-16 (Byte1~2)，整帧 16 字节全部参与运算
        # raw 中 Byte1~2 此时为 0x00，CRC 计算后再填充
        crc = _crc16_ccitt(bytes(raw))
        struct.pack_into('>H', raw, 1, crc)

        self._log(f"[SYNC] 发送时间同步帧 seq={self._seq_counter} "
                  f"s={seconds} ns={nanos} crc=0x{crc:04X}", "SEND")

        # 构造 CANFD 扩展帧，CAN ID = 0x0400，16 字节数据
        msg = can.Message(
            arbitration_id=0x0400,
            data=bytes(raw),
            is_extended_id=True,
            is_fd=True,
            dlc=16,
        )
        self.bus.send(msg)

        # 序列号递增，0~255 循环
        self._seq_counter = (self._seq_counter + 1) & 0xFF

        # 帧末尾输出空行，利于 GUI 日志阅读
        self._log("", "INFO")
