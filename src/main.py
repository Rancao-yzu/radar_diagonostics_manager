# -*- coding: utf-8 -*-
"""雷达诊断管理程序入口 —— 启动 GUI 并绑定事件"""
from datetime import datetime
import sys
import os
import threading
import tkinter as tk

# 将 lib/ 目录加入搜索路径，确保使用项目内置的 isotp/uds 库
# 开发环境和 PyInstaller 打包后都能正确找到 lib/ 路径
if getattr(sys, 'frozen', False):
    _BASE_DIR = sys._MEIPASS
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_BASE_DIR, 'lib'))

from gui_main import RadarDiagnosticsGUI
from can_config import check_can_interfaces
from calibration import CalibrationManager, _load_can_ids, OAResultReceiver
from sync import TimeSyncManager
from dtc import DTCManager, load_dtc_config
from ota.version_query import query_version, DID_SOFTWARE, DID_HARDWARE
import can
from bus_recorder import BusRecorder


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
        # OA 双通道：主通道和标定专用第二通道
        self._oa_mgr = None
        self._oa_bus2 = None
        self._oa_mgr2 = None

        self._bind_events()

    def _bind_events(self):
        """将 GUI 按钮点击事件绑定到对应的处理方法"""
        # 侧栏导航按钮 —— 切换功能面板
        self.gui.btn_ota._command = self.gui._show_ota_panel
        self.gui.btn_dtc._command = self.gui._show_dtc_panel
        self.gui.btn_cal._command = self.gui._show_cal_panel
        self.gui.btn_oa._command = self.gui._show_oa_panel

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

        # 时间同步复选框
        self.gui.chk_time_sync.configure(command=self._on_time_sync_toggle)

        # DTC 按钮
        self.gui.btn_dtc_start._command = self._on_dtc_start

        # OA 结果接收按钮
        self.gui.btn_oa_start._command = self._on_oa_start
        # OA 第二通道连接/断开按钮
        self.gui.btn_oa_connect2._command = self._on_oa_connect2
        self.gui.btn_oa_disconnect2._command = self._on_oa_disconnect2

        # 版本查询按钮
        self.gui.btn_ver_fl._command = lambda: self._on_query_version('FL')
        self.gui.btn_ver_fr._command = lambda: self._on_query_version('FR')

        # 窗口关闭回调
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _get_cal_mgr(self):
        """懒加载标定管理器，未连接时提示并返回 None"""
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
            self.gui.log("[INFO] 时间同步已启动", "OK")
        else:
            self._stop_time_sync()
            self.gui.log("[INFO] 时间同步已停止", "OK")

    def _start_time_sync(self):
        """每 X 秒发送一次时间同步帧，通过 after 递归调度"""
        mgr = self._get_sync_mgr()
        if mgr is None:
            self.gui.time_sync_var.set(False)
            return
        mgr.build_and_send()
        # 每 x 秒发送一次时间同步帧  现定为66ms×6=396ms
        self._sync_timer_id = self.root.after(396, self._start_time_sync)

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
        """静态标定 按钮的实例"""
        mgr = self._get_cal_mgr()
        if mgr is None:
            return
        mgr.static_calibration(radar_index)

    def _on_send_params(self, radar_index):
        """发送参数 按钮的实例"""
        mgr = self._get_cal_mgr()
        if mgr is None:
            return
        mgr.send_params(radar_index)

    def _on_clear_params(self, radar_index):
        """清除参数 按钮的实例"""
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
        # 配置 CAN 总线过滤器，标定相关 CAN ID
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

        # 版本号读取相关 CAN ID
        for can_id in (0x74E, 0x74F, 0x78E, 0x78F):
            filters.append({"can_id": can_id, "can_mask": 0x7FF, "extended": False})

        dtc_ids = load_dtc_config()['can_ids']
        # 配置 CAN 总线过滤器，DTC 相关 CAN ID
        for key, can_id in dtc_ids.items():
            filters.append({"can_id": can_id, "can_mask": 0x7FF, "extended": False})
            
        # OA 结果 CAN ID
        for oa_id in (1502, 1470, 1454, 1486):
            filters.append({"can_id": oa_id, "can_mask": 0x7FF, "extended": False})
        self.gui.log(f"[INFO] CAN 总线过滤器: {filters}", "INFO")
        
        # 连接 CAN 总线，整个项目的唯一实例!!!!
        self._bus = can.interface.Bus(
            interface="kvaser",
            channel=self.gui.get_channel_number(),
            bitrate=int(bitrate),
            data_bitrate=int(data_bitrate),
            fd=True,
            can_filters=filters,
        )
        # BusRecorder 透明代理，recv 后自动写
        asc_path = os.path.join('OUT', datetime.now().strftime('%Y%m%d%H%M%S') + '.asc')
        os.makedirs('OUT', exist_ok=True)
        self._bus = BusRecorder(self._bus, asc_path)
        # 重置各种管理器和实例状态
        self._cal_mgr = None
        self._sync_mgr = None
        self._stop_time_sync()
        self._stop_dtc()
        self._dtc_mgr = None
        self._stop_oa()
        self._oa_mgr = None
        self.gui.time_sync_var.set(False)
        self.gui.set_connection_status(True)
        self.gui.log(f"[OK] 已连接 — Channel: {channel}, Bitrate: {bitrate}, Data Bitrate: {data_bitrate}", "OK")

    def _on_close(self):
        self._stop_time_sync()
        self._stop_dtc()
        self._stop_oa()
        self._on_oa_disconnect2()
        self.gui.download_log()  # 关闭前自动保存日志
        if self._bus is not None:
            self._bus.shutdown()
        self.root.destroy()

    def _on_oa_start(self):
        """启动 OA 结果接收器（支持双通道）"""
        if self._bus is None:
            self.gui.log('[OA WARN] 请先连接 CAN 总线', 'ERROR')
            return
        # 主通道 OA 接收器
        if self._oa_mgr is None:
            self._oa_mgr = OAResultReceiver(self._bus, log_callback=self.gui.log,
                                            data_callback=self._on_oa_data)
        self._oa_mgr.start()
        # 第二通道 OA 接收器（OA 标定专用）
        if self._oa_bus2 is not None:
            if self._oa_mgr2 is None:
                self._oa_mgr2 = OAResultReceiver(self._oa_bus2, log_callback=self.gui.log,
                                                 data_callback=self._on_oa_data)
            self._oa_mgr2.start()
        self.gui.oa_set_buttons_state(True)
        # 3 秒后自动停止
        threading.Timer(3.0, self._stop_oa).start()

    def _on_oa_connect2(self):
        """连接 OA 第二通道"""
        channel = self.gui.oa_get_channel2_number()
        if not channel:
            self.gui.log('[OA WARN] 请先选择第二通道', 'ERROR')
            return
        # 断开旧连接
        self._on_oa_disconnect2()
        # 从主通道配置获取 bitrate 设置
        _, bitrate, data_bitrate = self.gui.get_channel_info()
        if not bitrate or not data_bitrate:
            self.gui.log('[OA WARN] 请先在 CAN 配置中设置波特率', 'ERROR')
            return
        # 第二通道只监听 OA 4 个 CAN ID
        oa_filters = [{"can_id": cid, "can_mask": 0x7FF, "extended": False}
                      for cid in (1502, 1470, 1454, 1486)]
        self.gui.log(f"[INFO] 第二通道 CAN 过滤器: {oa_filters}", "INFO")
        try:
            self._oa_bus2 = can.interface.Bus(
                interface="kvaser",
                channel=int(channel),
                bitrate=int(bitrate),
                data_bitrate=int(data_bitrate),
                fd=True,
                can_filters=oa_filters,
            )
        except Exception as e:
            self.gui.log(f'[OA ERROR] 第二通道连接失败: {e}', 'ERROR')
            self._oa_bus2 = None
            return
        self.gui.oa_set_chan2_state(True)
        self.gui.log(f'[OA] 第二通道已连接 — Channel: {channel}', 'OK')

    def _on_oa_disconnect2(self):
        """断开 OA 第二通道"""
        if self._oa_bus2 is not None:
            self._oa_bus2.shutdown()
            self._oa_bus2 = None
            self.gui.log('[OA] 第二通道已断开', 'INFO')

        self.gui.oa_set_chan2_state(False)

    def _on_oa_data(self, node, data):
        """OA 数据回调（接收线程中调用，通过 idle 切回主线程更新表格）"""
        self.gui.root.after_idle(lambda: self.gui.oa_update_table(node, data))

    def _stop_oa(self):
        """停止 OA 结果接收器（停所有通道）"""
        if self._oa_mgr is not None:
            self._oa_mgr.stop()
            self._oa_mgr = None
        if self._oa_mgr2 is not None:
            self._oa_mgr2.stop()
            self._oa_mgr2 = None
        self.gui.oa_set_buttons_state(False)

    def _on_dtc_start(self):
        """启动 DTC 管理器 按钮的实例"""
        if self._bus is None:
            self.gui.log('[DTC WARN] 请先连接 CAN 总线', 'ERROR')
            return
        if self._dtc_mgr is None:
            self._dtc_mgr = DTCManager(self._bus, log_callback=self.gui.log)
        self._dtc_mgr.start()
        self.gui.dtc_set_buttons_state(True)
        self._dtc_refresh_table()
        # 2 秒后自动关闭
        self.root.after(2000, self._stop_dtc)

    def _stop_dtc(self):
        """停止 DTC 管理器 按钮的实例"""
        if self._dtc_refresh_id is not None:
            self.root.after_cancel(self._dtc_refresh_id)
            self._dtc_refresh_id = None
        if self._dtc_mgr is not None:
            self._dtc_mgr.stop()
        self.gui.dtc_set_buttons_state(False)

    def _dtc_refresh_table(self):
        """刷新 DTC 表格数据"""
        if self._dtc_mgr is not None and self._dtc_mgr.is_running():
            data = self._dtc_mgr.get_all_data()
            self.gui.dtc_update_table(data)
            self._dtc_refresh_id = self.root.after(500, self._dtc_refresh_table)

    def _on_query_version(self, radar):
        """查询雷达软硬件版本号"""
        if self._bus is None:
            self.gui.log('[版本查询] 请先连接 CAN 总线', 'ERROR')
            return

        def _do_query():
            sw = query_version(self._bus, radar, DID_SOFTWARE, log_callback=self.gui.log)
            hw = query_version(self._bus, radar, DID_HARDWARE, log_callback=self.gui.log)
            self.root.after_idle(lambda: self._update_version_ui(radar, sw, hw))

        self.gui.btn_ver_fl.configure(state=tk.DISABLED)
        self.gui.btn_ver_fr.configure(state=tk.DISABLED)
        threading.Thread(target=_do_query, daemon=True).start()
        # 2.5s 后恢复按钮
        self.root.after(2500, lambda: self.gui.btn_ver_fl.configure(state=tk.NORMAL))
        self.root.after(2500, lambda: self.gui.btn_ver_fr.configure(state=tk.NORMAL))

    def _update_version_ui(self, radar, sw, hw):
        """更新版本查询 UI 显示"""
        sw_str = f"软件版本: {sw}" if sw else "软件版本: 查询失败"
        hw_str = f"硬件版本: {hw}" if hw else "硬件版本: 查询失败"
        if radar == 'FL':
            self.gui.ver_fl_sw_var.set(sw_str)
            self.gui.ver_fl_hw_var.set(hw_str)
        else:
            self.gui.ver_fr_sw_var.set(sw_str)
            self.gui.ver_fr_hw_var.set(hw_str)

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
