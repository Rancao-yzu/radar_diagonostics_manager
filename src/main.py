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
from sync import TimeSyncManager
from dtc import DTCManager, load_dtc_config
import can

class Application:
    """应用程序主类：创建 GUI 实例，绑定按钮事件"""

    def __init__(self):
        self.root = tk.Tk()
        self.gui = RadarDiagnosticsGUI(self.root)
        self._bus = None
        self._cal_mgr = None
        self._sync_mgr = None
        self._sync_timer_id = None
        self._dtc_mgr = None
        self._dtc_refresh_id = None

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
        self.gui.btn_static_1.configure(command=lambda: self._cal_action(self._on_static_cal, 1))
        self.gui.btn_static_2.configure(command=lambda: self._cal_action(self._on_static_cal, 2))
        self.gui.btn_static_3.configure(command=lambda: self._cal_action(self._on_static_cal, 3))
        self.gui.btn_static_4.configure(command=lambda: self._cal_action(self._on_static_cal, 4))
        self.gui.btn_param_1.configure(command=lambda: self._cal_action(self._on_send_params, 1))
        self.gui.btn_param_2.configure(command=lambda: self._cal_action(self._on_send_params, 2))
        self.gui.btn_param_3.configure(command=lambda: self._cal_action(self._on_send_params, 3))
        self.gui.btn_param_4.configure(command=lambda: self._cal_action(self._on_send_params, 4))
        self.gui.btn_clear_1.configure(command=lambda: self._cal_action(self._on_clear_params, 1))
        self.gui.btn_clear_2.configure(command=lambda: self._cal_action(self._on_clear_params, 2))
        self.gui.btn_clear_3.configure(command=lambda: self._cal_action(self._on_clear_params, 3))
        self.gui.btn_clear_4.configure(command=lambda: self._cal_action(self._on_clear_params, 4))

        # 日志下载按钮
        self.gui.btn_download_log.configure(command=self.gui.download_log)

        # 时间同步复选框
        self.gui.chk_time_sync.configure(command=self._on_time_sync_toggle)

        # DTC 按钮
        self.gui.btn_dtc_start._command = self._on_dtc_start
        self.gui.btn_dtc_stop._command = self._stop_dtc

        # 窗口关闭回调
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _get_cal_mgr(self):
        if self._cal_mgr is None:
            if self._bus is None:
                self.gui.log("[WARN] 请先点击连接按钮", "ERROR")
                return None
            self._cal_mgr = CalibrationManager(self._bus, log_callback=self.gui.log)
        return self._cal_mgr

    def _get_sync_mgr(self):
        """懒加载时间同步管理器，未连接时提示并返回 None"""
        if self._sync_mgr is None:
            if self._bus is None:
                self.gui.log("[WARN] 请先点击连接按钮", "ERROR")
                return None
            self._sync_mgr = TimeSyncManager(self._bus, log_callback=self.gui.log)
        return self._sync_mgr

    def _on_time_sync_toggle(self):
        """勾选框状态变化回调：勾选 → 启动定时发送，取消 → 停止"""
        if self.gui.time_sync_var.get():
            self._start_time_sync()
        else:
            self._stop_time_sync()

    def _start_time_sync(self):
        """每 1 秒发送一次时间同步帧，通过 after 递归调度"""
        mgr = self._get_sync_mgr()
        if mgr is None:
            self.gui.time_sync_var.set(False)
            return
        mgr.build_and_send()
        # 每 1 秒发送一次时间同步帧
        self._sync_timer_id = self.root.after(1000, self._start_time_sync)

    def _stop_time_sync(self):
        """取消 after 定时器，停止时间同步"""
        if self._sync_timer_id is not None:
            self.root.after_cancel(self._sync_timer_id)
            self._sync_timer_id = None

    def _cal_action(self, target, *args):
        """执行标定操作，禁用按钮，完成后启用"""
        self.gui._set_cal_buttons_state(tk.DISABLED)
        threading.Thread(target=target, args=args, daemon=True).start()
        # 等待标定操作完成,1500ms 后启用按钮状态
        self.root.after(1500, lambda: self.gui._set_cal_buttons_state(tk.NORMAL))

    def _on_static_cal(self, radar_index):
        mgr = self._get_cal_mgr()
        if mgr is None:
            return
        mgr.static_calibration(radar_index)

    def _on_send_params(self, radar_index):
        mgr = self._get_cal_mgr()
        if mgr is None:
            return
        mgr.send_params(radar_index)

    def _on_clear_params(self, radar_index):
        mgr = self._get_cal_mgr()
        if mgr is None:
            return
        mgr.clear_params(radar_index)

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
            {"can_id": ids['left_front_static_recv'], "can_mask": 0x7FF, "extended": False},
            {"can_id": ids['right_front_static_recv'], "can_mask": 0x7FF, "extended": False},
            {"can_id": ids['left_rear_static_recv'], "can_mask": 0x7FF, "extended": False},
            {"can_id": ids['right_rear_static_recv'], "can_mask": 0x7FF, "extended": False},
            {"can_id": ids['left_front_param_recv'], "can_mask": 0x7FF, "extended": False},
            {"can_id": ids['right_front_param_recv'], "can_mask": 0x7FF, "extended": False},
            {"can_id": ids['left_rear_param_recv'], "can_mask": 0x7FF, "extended": False},
            {"can_id": ids['right_rear_param_recv'], "can_mask": 0x7FF, "extended": False},
        ]

        dtc_ids = load_dtc_config()['can_ids']
        for key, can_id in dtc_ids.items():
            filters.append({"can_id": can_id, "can_mask": 0x7FF, "extended": False})
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
        self._sync_mgr = None
        self._stop_time_sync()
        self._stop_dtc()
        self._dtc_mgr = None
        self.gui.time_sync_var.set(False)
        self.gui.set_connection_status(True)
        self.gui.log(f"[OK] 已连接 — Channel: {channel}, Bitrate: {bitrate}, Data Bitrate: {data_bitrate}", "OK")

    def _on_close(self):
        self._stop_time_sync()
        self._stop_dtc()
        if self._bus is not None:
            self._bus.shutdown()
        self.root.destroy()

    def _on_dtc_start(self):
        if self._bus is None:
            self.gui.log('[DTC WARN] 请先连接 CAN 总线', 'ERROR')
            return
        if self._dtc_mgr is None:
            self._dtc_mgr = DTCManager(self._bus, log_callback=self.gui.log)
        self._dtc_mgr.start()
        self.gui.dtc_set_buttons_state(True)
        self._dtc_refresh_table()

    def _stop_dtc(self):
        if self._dtc_refresh_id is not None:
            self.root.after_cancel(self._dtc_refresh_id)
            self._dtc_refresh_id = None
        if self._dtc_mgr is not None:
            self._dtc_mgr.stop()
        self.gui.dtc_set_buttons_state(False)
        self.gui.dtc_update_table(None)

    def _dtc_refresh_table(self):
        if self._dtc_mgr is not None and self._dtc_mgr.is_running():
            data = self._dtc_mgr.get_all_data()
            self.gui.dtc_update_table(data)
            self._dtc_refresh_id = self.root.after(500, self._dtc_refresh_table)

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
