# -*- coding: utf-8 -*-
import sys
import os
import time
import struct
import configparser
import threading
import can

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'lib'))

# 超时时间定义
CAL_TIMEOUT_PARAM = 3.5

# CAN 配置文件路径
_CAL_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'config', 'config_c.ini'
)

# 加载 CAN ID 配置
def _load_can_ids():
    cfg = configparser.ConfigParser()
    cfg.read(_CAL_CONFIG_PATH, encoding='utf-8')
    return {
        'left_static_send':  int(cfg.get('CAN', 'left_static_send_id'), 0),
        'left_static_recv':  int(cfg.get('CAN', 'left_static_recv_id'), 0),
        'right_static_send': int(cfg.get('CAN', 'right_static_send_id'), 0),
        'right_static_recv': int(cfg.get('CAN', 'right_static_recv_id'), 0),
        'left_param_send':   int(cfg.get('CAN', 'left_param_send_id'), 0),
        'left_param_recv':   int(cfg.get('CAN', 'left_param_recv_id'), 0),
        'right_param_send':  int(cfg.get('CAN', 'right_param_send_id'), 0),
        'right_param_recv':  int(cfg.get('CAN', 'right_param_recv_id'), 0),
    }

def _clean_val(cfg, section, key):
    val = cfg.get(section, key)
    for ch in (';', '#'):
        idx = val.find(ch)
        if idx != -1:
            val = val[:idx]
    return val.strip()

# 参数数据格式：7个float（大端序）
PARAM_STRUCT = struct.Struct('>fffffff')

RESULT_STATUS_MAP = {
    1: "结果合格",
    2: "结果不合格",
    3: "标定进行中",
}

ERROR_CODE_MAP = {
    0: "标定进行中无错误码",
    1: "标定未成功触发",
    2: "flash存储失败",
    3: "车速超限",
    4: "角度过大",
    5: "角度过小",
    6: "目标数异常",
    7: "超时",
    8: "执行成功",
}


class CalibrationManager:
    def __init__(self, channel, bitrate, data_bitrate, log_callback=None):
        """初始化标定管理器"""
        self.channel = int(channel)
        self.bitrate = int(bitrate)
        self.data_bitrate = int(data_bitrate)
        self.log_callback = log_callback
        self.bus = None
        self._running = False
        self._can_ids = _load_can_ids()

    def _log(self, msg, tag="INFO"):
        """日志记录器"""
        print(msg)
        if self.log_callback:
            self.log_callback(msg, tag)

    def connect(self):
        """连接CAN总线"""
        ids = self._can_ids
        filters = [
            {"can_id": ids['left_static_recv'], "can_mask": 0x7FF, "extended": False},
            {"can_id": ids['right_static_recv'], "can_mask": 0x7FF, "extended": False},
            {"can_id": ids['left_param_recv'], "can_mask": 0x7FF, "extended": False},
            {"can_id": ids['right_param_recv'], "can_mask": 0x7FF, "extended": False},
        ]
        self.bus = can.interface.Bus(
            interface="kvaser",
            channel=self.channel,
            bitrate=self.bitrate,
            data_bitrate=self.data_bitrate,
            fd=True,
            can_filters=filters,
        )
        self._log(f"[CAL] CAN 总线已连接 channel={self.channel} bitrate={self.bitrate} data_bitrate={self.data_bitrate}", "OK")

    def disconnect(self):
        """断开CAN总线"""
        if self.bus:
            self.bus.shutdown()
            self.bus = None
            self._log("[CAL] CAN 总线已断开", "INFO")

    def _send_and_wait(self, send_id, send_data, expect_recv_id, expect_data, timeout, keep_alive_data=None):
        """
        发送CAN消息并等待响应
            
        Args:
            send_id: 发送消息的CAN ID
            send_data: 待发送的数据（bytes或list，最多64字节）
            expect_recv_id: 期望接收的响应CAN ID
            expect_data: 期望响应的数据
            timeout: 等待响应的超时时间（秒）
            keep_alive_data: 可选，后台轮询发送的保活数据，每0.5秒发送一次
        """
        stop_poll = threading.Event() # 1 创建事件，初始False

        def _bg_poll():
            # 2 后台轮询线程
            while not stop_poll.is_set():# 2 检查事件是否为True
                msg = can.Message(
                    arbitration_id=send_id, data=keep_alive_data,
                    is_extended_id=False, is_fd=True, dlc=len(keep_alive_data),
                )
                self.bus.send(msg)
                stop_poll.wait(0.5)# 3 等待最多0.5秒，如果事件被set则立即退出

        if keep_alive_data is not None:
            threading.Thread(target=_bg_poll, daemon=True).start()
            self._log(f"[INFO] 启台轮询 0x{send_id:03X} Data={keep_alive_data}", "INFO")

        try:
            msg = can.Message(
                arbitration_id=send_id, 
                data=send_data[:64], 
                is_extended_id=False, 
                is_fd=True, 
                dlc=len(send_data)
            )
            self.bus.send(msg)
            self._log(f"[SEND] ID=0x{send_id:03X} DLC={len(send_data)} Data={send_data}", "SEND")

            deadline = time.time() + timeout
            while time.time() < deadline:
                remaining = deadline - time.time()
                recv = self.bus.recv(timeout=min(remaining, 0.1))
                if recv is None:
                    continue
                if recv.arbitration_id == expect_recv_id and list(recv.data[:len(expect_data)]) == expect_data:
                    # 检查响应是否匹配
                    self._log(f"[RECV] ID=0x{recv.arbitration_id:03X} Data={[hex(b) for b in recv.data]}", "RECV")
                    return recv

            self._log(f"[ERROR] 等待响应超时 ID=0x{expect_recv_id:03X}", "ERROR")
            return None
        finally:
            if keep_alive_data is not None: # 4 通知后台线程停止
                stop_poll.set()

    def static_calibration(self, is_right_radar):
        """静态标定"""
        send_id = self._can_ids['right_static_send'] if is_right_radar else self._can_ids['left_static_send']
        recv_id = self._can_ids['right_static_recv'] if is_right_radar else self._can_ids['left_static_recv']

        radar_name = "右雷达" if is_right_radar else "左雷达"
        self._log(f"[INFO] 开始{radar_name}静态标定...", "INFO")

        resp = self._send_and_wait(send_id, [0x02], recv_id, [0x02, 0x01], CAL_TIMEOUT_PARAM, keep_alive_data=[0x00])
        if resp is None:
            self._log(f"[ERROR] {radar_name}静态标定启动失败", "ERROR")
            return

        self._log(f"[INFO] {radar_name}标定已启动，等待查询结果...", "INFO")

        deadline = time.time() + CAL_TIMEOUT_PARAM
        while time.time() < deadline:
            remaining = deadline - time.time()
            recv = self.bus.recv(timeout=min(remaining, 0.1))
            if recv is None:
                continue
            self._log(f"[RECV] ID=0x{recv.arbitration_id:03X} Data={[hex(b) for b in recv.data]}", "RECV")
            if recv.arbitration_id == recv_id and len(recv.data) >= 2 and recv.data[0] == 0x04:
                self._parse_cal_result(recv.data[1:])
                return

        self._log(f"[ERROR] {radar_name}标定结果等待超时", "ERROR")

    def _parse_cal_result(self, data):
        """解析标定结果数据"""
        if len(data) < 8:
            self._log("[ERROR] 标定结果数据长度不足", "ERROR")
            return

        cal_result = struct.unpack('>H', data[0:2])[0]   # 校准判定结果 (2字节)
        error_code = struct.unpack('>H', data[2:4])[0]   # 流程运行工况 (2字节)

        self._log(f"[OK] 标定结果解析:", "OK")
        self._log(f"  标定结果: {RESULT_STATUS_MAP.get(cal_result, f'未知({cal_result})')}", "OK")
        self._log(f"  标定状态: {ERROR_CODE_MAP.get(error_code, f'未知({error_code})')}", "OK")

    def _read_cal_params(self, is_right_radar):
        section = 'RightRadar' if is_right_radar else 'LeftRadar'
        radar_name = "右雷达" if is_right_radar else "左雷达"

        cfg = configparser.ConfigParser()
        if not os.path.exists(_CAL_CONFIG_PATH):
            self._log(f"[ERROR] 配置文件不存在: {_CAL_CONFIG_PATH}", "ERROR")
            return None

        cfg.read(_CAL_CONFIG_PATH, encoding='utf-8')
        if section not in cfg:
            self._log(f"[ERROR] 配置文件中未找到 [{section}] 节", "ERROR")
            return None

        try:
            params = {
                'vehicle_height': float(_clean_val(cfg, section, 'vehicle_height')),
                'x_offset':       float(_clean_val(cfg, section, 'x_offset')),
                'y_offset':       float(_clean_val(cfg, section, 'y_offset')),
                'z_offset':       float(_clean_val(cfg, section, 'z_offset')),
                'yaw_angle':      float(_clean_val(cfg, section, 'yaw_angle')),
                'pitch_angle':    float(_clean_val(cfg, section, 'pitch_angle')),
                'roll_angle':     float(_clean_val(cfg, section, 'roll_angle')),
            }
        except (configparser.NoOptionError, ValueError) as e:
            self._log(f"[ERROR] 读取{radar_name}标定参数失败: {e}", "ERROR")
            return None

        self._log(f"[OK] 从配置文件读取{radar_name}参数: "
                  f"vh={params['vehicle_height']:.2f} x={params['x_offset']:.2f} "
                  f"y={params['y_offset']:.2f} z={params['z_offset']:.2f} "
                  f"yaw={params['yaw_angle']:.2f} pitch={params['pitch_angle']:.2f} "
                  f"roll={params['roll_angle']:.2f}", "OK")
        return params

    def send_params(self, is_right_radar):
        """下发标定参数"""
        params = self._read_cal_params(is_right_radar)
        if params is None:
            return False

        send_id = self._can_ids['right_param_send'] if is_right_radar else self._can_ids['left_param_send']
        recv_id = self._can_ids['right_param_recv'] if is_right_radar else self._can_ids['left_param_recv']
        radar_name = "右雷达" if is_right_radar else "左雷达"

        # 构建参数数据包
        packed = PARAM_STRUCT.pack(
            params['vehicle_height'],
            params['x_offset'], params['y_offset'], params['z_offset'],
            params['yaw_angle'], params['pitch_angle'], params['roll_angle'],
        )
        data = [0x01] + list(packed) + [0x00] * 35

        self._log(f"[INFO] 向{radar_name}下发标定参数...", "INFO")
        resp = self._send_and_wait(send_id, data, recv_id, [0x01, 0x01], CAL_TIMEOUT_PARAM)
        if resp is None:
            self._log(f"[ERROR] {radar_name}参数下发失败", "ERROR")
            return False

        self._log(f"[OK] {radar_name}参数下发成功", "OK")
        return True

    def clear_params(self, is_right_radar):
        """清除标定参数"""
        send_id = self._can_ids['right_param_send'] if is_right_radar else self._can_ids['left_param_send']
        recv_id = self._can_ids['right_param_recv'] if is_right_radar else self._can_ids['left_param_recv']
        radar_name = "右雷达" if is_right_radar else "左雷达"

        self._log(f"[INFO] 清除{radar_name}标定参数...", "INFO")
        resp = self._send_and_wait(send_id, [0x02], recv_id, [0x02, 0x01], CAL_TIMEOUT_PARAM)
        if resp is None:
            self._log(f"[ERROR] {radar_name}参数清除失败", "ERROR")
            return False

        self._log(f"[OK] {radar_name}参数清除成功", "OK")
        return True
