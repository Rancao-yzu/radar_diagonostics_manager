# -*- coding: utf-8 -*-
"""透明代理：recv/send 透传真实总线，recv 取到消息后自动写"""
import can


class BusRecorder:

    def __init__(self, bus, blf_path):
        self._bus = bus
        self._logger = can.Logger(blf_path)

    def recv(self, timeout=None):
        msg = self._bus.recv(timeout=timeout)
        if msg is not None:
            self._logger(msg)
        return msg

    def send(self, msg, timeout=None):
        self._logger(msg)
        self._bus.send(msg, timeout=timeout)

    def shutdown(self):
        self._logger.stop()
        self._bus.shutdown()

    def __getattr__(self, name):
        return getattr(self._bus, name)
