# -*- coding: utf-8 -*-
"""雷达诊断管理程序入口 —— 启动 GUI 并绑定事件"""
import sys
import os
import threading
import tkinter as tk

# 将 lib/ 目录加入搜索路径，确保使用项目内置的 isotp/uds 库
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))

from gui_main import RadarDiagnosticsGUI
from can_config import check_can_interfaces
from calibration import CalibrationManager, _load_can_ids
import can

class Application:
    """应用程序主类：创建 GUI 实例，绑定按钮事件"""

    def __init__(self):
        self.root = tk.Tk()
        self.gui = RadarDiagnosticsGUI(self.root)
        self._bus = None
        self._cal_mgr = None

        self._bind_events()

    def _bind_events(self):
        """将 GUI 按钮点击事件绑定到对应的处理方法"""
        # 侧栏导航按钮 —— 切换功能面板
        self.gui.btn_ota._command = self.gui._show_ota_panel
        self.gui.btn_dtc._command = self.gui._show_dtc_panel
        self.gui.btn_cal._command = self.gui._show_cal_panel

        # 刷新通道按钮
        self.gui.btn_connect.configure(command=self._on_connect)
        self.gui.btn_refresh.configure(command=self._refresh_channels)

        # 标定功能按钮
        self.gui.btn_static_left.configure(command=lambda: self._cal_action(self._on_static_cal, False))
        self.gui.btn_static_right.configure(command=lambda: self._cal_action(self._on_static_cal, True))
        self.gui.btn_param_left.configure(command=lambda: self._cal_action(self._on_send_params, False))
        self.gui.btn_param_right.configure(command=lambda: self._cal_action(self._on_send_params, True))
        self.gui.btn_clear_left.configure(command=lambda: self._cal_action(self._on_clear_params, False))
        self.gui.btn_clear_right.configure(command=lambda: self._cal_action(self._on_clear_params, True))

        # 日志下载按钮
        self.gui.btn_download_log.configure(command=self.gui.download_log)

        # 窗口关闭回调
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _get_cal_mgr(self):
        if self._cal_mgr is None:
            if self._bus is None:
                self.gui.log("[WARN] 请先点击连接按钮", "ERROR")
                return None
            self._cal_mgr = CalibrationManager(self._bus, log_callback=self.gui.log)
        return self._cal_mgr

    def _cal_action(self, target, *args):
        """执行标定操作，禁用按钮，完成后启用"""
        self.gui._set_cal_buttons_state(tk.DISABLED)
        threading.Thread(target=target, args=args, daemon=True).start()
        # 等待标定操作完成,1500ms 后启用按钮状态
        self.root.after(1500, lambda: self.gui._set_cal_buttons_state(tk.NORMAL))

    def _on_static_cal(self, is_right_radar):
        """触发静态标定"""
        mgr = self._get_cal_mgr()
        if mgr is None:
            return
        mgr.static_calibration(is_right_radar)

    def _on_send_params(self, is_right_radar):
        """发送标定参数"""
        mgr = self._get_cal_mgr()
        if mgr is None:
            return
        mgr.send_params(is_right_radar)

    def _on_clear_params(self, is_right_radar):
        """清除标定参数"""
        mgr = self._get_cal_mgr()
        if mgr is None:
            return
        mgr.clear_params(is_right_radar)

    def _on_connect(self):
        """连接CAN 通道 按钮的实例"""
        channel, bitrate, data_bitrate = self.gui.get_channel_info()
        if not channel or not bitrate or not data_bitrate:
            self.gui.log("[WARN] 请先选择 CAN 通道、波特率和数据波特率", "ERROR")
            return
        
        if self._bus is not None:
            self._bus.shutdown()
            self._bus = None
            self.gui.log("[INFO] CAN 总线已断开", "INFO")
        
        ids = _load_can_ids()
        filters = [
            {"can_id": ids['left_static_recv'], "can_mask": 0x7FF, "extended": False},
            {"can_id": ids['right_static_recv'], "can_mask": 0x7FF, "extended": False},
            {"can_id": ids['left_param_recv'], "can_mask": 0x7FF, "extended": False},
            {"can_id": ids['right_param_recv'], "can_mask": 0x7FF, "extended": False},
        ]
        self.gui.log(f"[INFO] CAN 总线过滤器: {filters}", "INFO")
        
        self._bus = can.interface.Bus(
            interface="kvaser",
            channel=self.gui.get_channel_number(),
            bitrate=int(bitrate),
            data_bitrate=int(data_bitrate),
            fd=True,
            can_filters=filters,
        )
        self._cal_mgr = None
        self.gui.set_connection_status(True)
        self.gui.log(f"[OK] 已连接 — Channel: {channel}, Bitrate: {bitrate}, Data Bitrate: {data_bitrate}", "OK")

    def _on_close(self):
        if self._bus is not None:
            self._bus.shutdown()
        self.root.destroy()

    def _refresh_channels(self):
        """扫描可用 CAN 通道，更新下拉列表，完成后恢复鼠标样式"""
        self.gui.root.config(cursor="watch")
        self.gui.root.update()
        try:
            interfaces = check_can_interfaces()
            if interfaces:
                self.gui.set_channel_list(interfaces)
                self.gui.log(f"[INFO] 检测到 {len(interfaces)} 个 CAN 通道", "INFO")
            else:
                self.gui.set_channel_list([])
                self.gui.log("[WARN] 未检测到 CAN 硬件接口", "ERROR")
        finally:
            self.gui.root.config(cursor="")

    def run(self):
        """启动 Tkinter 主事件循环"""
        self.root.mainloop()


if __name__ == "__main__":
    app = Application()
    app.run()
