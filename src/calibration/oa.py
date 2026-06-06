# -*- coding: utf-8 -*-
"""OA 结果接收模块 —— 监听四轮雷达 FrameHeader 消息，用 DBC 解析信号并输出到日志"""
import os
import threading
import cantools
import can

# DBC 文件路径
_DBC_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'images', 'MCR1+MFR1+objects_list CAN Matrix to Zelos_V3.0.2_03_TX.dbc'
)

# OA 结果 CAN ID 映射（来自 DBC）
_OA_CAN_IDS = {
    1502: "RR",   # FrameHeader_RR
    1470: "RL",   # FrameHeader_RL
    1454: "FR",   # FrameHeader_FR
    1486: "FL",   # FrameHeader_FL
}


class OAResultReceiver:
    """OA 结果接收器 — 监听四轮雷达 FrameHeader，DBC 解析后输出到日志"""

    def __init__(self, bus: can.BusABC, log_callback=None):
        self.bus = bus
        self.log_callback = log_callback
        self._running = False
        self._thread = None
        db = cantools.database.load_file(_DBC_PATH)
        # 预缓存 4 个关心的 CAN ID 对应的 message 对象，避免每次解码时遍历整个 DBC
        self._msg_cache = {}
        for can_id in _OA_CAN_IDS:
            try:
                self._msg_cache[can_id] = db.get_message_by_frame_id(can_id)
                self._log(f'[OA] 缓存 message {self._msg_cache[can_id]}')
            except Exception as e:
                self._log(f'[OA WARN] DBC 中未找到 CAN ID=0x{can_id:03X}: {e}')

    def _log(self, msg, tag='INFO'):
        """日志记录器"""
        print(msg)
        if self.log_callback:
            self.log_callback(msg, tag)

    def start(self):
        """启动接收线程"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._thread.start()
        self._log('[OA] 开始接收 OA 结果', 'OK')

    def stop(self):
        """停止接收线程"""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._log('[OA] 停止接收 OA 结果', 'INFO')

    def is_running(self):
        """检查接收线程是否正在运行"""
        return self._running

    def _receive_loop(self):
        """接收线程主循环"""
        while self._running:
            try:
                msg = self.bus.recv(timeout=0.5)
            except Exception as e:
                print(f'[OA ERROR] 接收消息异常: {e}')
                continue

            if msg is None:
                continue

            can_id = msg.arbitration_id
            cached_msg = self._msg_cache.get(can_id)
            if cached_msg is None:
                continue

            try:
                decoded = cached_msg.decode(msg.data)
            except Exception as e:
                print(f'[OA ERROR] DBC 解析失败 can_id=0x{can_id:03X}: {e}')
                continue

            node = _OA_CAN_IDS[can_id]  # cached_msg 已确保 can_id 在映射中

            # 按逻辑分组输出核心信号
            parts = [f'[OA] {node}']
            for name, val in decoded.items():
                # 去掉 RSDS_XX_ 前缀，精简显示
                short = name.split('_', 2)[-1] if name.startswith('RSDS_') else name
                # EleOffset / AziOffset 弧度转角度
                if ('EleOffset' in name or 'AziOffset' in name) and isinstance(val, (int, float)):
                    val = round(val * 180.0 / 3.141, 4)
                if isinstance(val, float):
                    parts.append(f'{short}={val:.4f}')
                else:
                    parts.append(f'{short}={val}')
            self._log(' | '.join(parts), 'OK')
