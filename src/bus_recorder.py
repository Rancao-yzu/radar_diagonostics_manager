# -*- coding: utf-8 -*-
"""透明代理：recv/send 透传真实总线，recv 取到消息后自动写"""
import can
import time
import threading


class BusRecorder:

    def __init__(self, bus, blf_path):
        self._bus = bus
        self._logger = can.Logger(blf_path)
        # can.Logger (ASCWriter) 非线程安全，多线程 recv/send 并发写入会破坏文件
        self._lock = threading.Lock()

    def recv(self, timeout=None):
        msg = self._bus.recv(timeout=timeout)
        if msg is not None:
            msg.is_rx = True
            with self._lock:
                self._logger(msg)
        return msg

    def send(self, msg, timeout=None):
        msg.is_rx = False
        msg.timestamp = time.time()
        with self._lock:
            self._logger(msg)
        self._bus.send(msg, timeout=timeout)

    def shutdown(self):
        self._logger.stop()
        self._bus.shutdown()

    def __getattr__(self, name):
        return getattr(self._bus, name)
