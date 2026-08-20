# -*- coding: utf-8 -*-
"""双通道 CAN 路由器 —— 前角(FL/FR)走通道1、后角(RL/RR)走通道2。

对外呈现为单一总线：send 按 CAN ID 分发到对应物理总线，
recv 由后台线程合并两路消息。各功能模块无需感知双通道。
"""
import threading
import queue


class BusRouter:
    """路由总线：按仲裁 ID 在前/后两条物理总线间分发与合并。"""

    def __init__(self, front_bus, rear_bus, rear_ids):
        """
        Args:
            front_bus: 前角物理总线（通道1，FL/FR），可为 None
            rear_bus:  后角物理总线（通道2，RL/RR），可为 None
            rear_ids:  应发往后角总线的 CAN ID 集合，其余 ID 默认走前角
        """
        self._front = front_bus
        self._rear = rear_bus
        self._rear_ids = set(rear_ids)
        self._queue = queue.Queue()
        self._running = True
        # 为每条物理总线起一个抽水线程，把 recv 到的消息推入合并队列
        self._drainers = []
        for bus in (front_bus, rear_bus):
            if bus is None:
                continue
            t = threading.Thread(target=self._drain, args=(bus,), daemon=True)
            t.start()
            self._drainers.append(t)

    def _drain(self, bus):
        """持续从某条物理总线 recv 并入合并队列"""
        while self._running:
            try:
                msg = bus.recv(timeout=1.0)
            except Exception:
                # 总线关闭等异常：退出抽水循环
                break
            if msg is not None:
                self._queue.put(msg)

    def send(self, msg, timeout=None):
        """分发发送：双通道按 ID 路由，单通道时全部走已连的那条"""
        front, rear = self._front, self._rear
        if front is not None and rear is not None:
            # 双通道：后角 ID 走后角总线，其余走前角
            bus = rear if msg.arbitration_id in self._rear_ids else front
        elif front is not None:
            bus = front          # 仅前角
        elif rear is not None:
            bus = rear           # 仅后角
        else:
            return               # 无总线，丢弃
        bus.send(msg, timeout=timeout)

    def recv(self, timeout=None):
        """从合并队列取一条消息，超时返回 None"""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def shutdown(self):
        """停止抽水线程并关闭两条物理总线"""
        self._running = False
        for bus in (self._front, self._rear):
            if bus is None:
                continue
            try:
                bus.shutdown()
            except Exception:
                pass

    def __getattr__(self, name):
        # 兼容对总线其它属性的访问：优先委托前角，前角没有则委托后角
        if self._front is not None:
            try:
                return getattr(self._front, name)
            except AttributeError:
                pass  # 前角没有这个属性，继续查后角
        
        if self._rear is not None:
            return getattr(self._rear, name)
        
        # 两条总线都不存在或都没有该属性
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
