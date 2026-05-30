# -*- coding: utf-8 -*-
import sys
import os
import time
import struct
import configparser
import can

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'lib'))

# 超时时间定义
CAL_TIMEOUT_STATIC = 10.0
CAL_TIMEOUT_PARAM = 3.0

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

PROCESS_STATUS_MAP = {
    0: "进程未激活",
    1: "运行中",
    2: "flash写入失败",
    3: "正常完成",
    4: "进程中断",
}

RESULT_STATUS_MAP = {
    0: "无校准结果",
    1: "结果超限",
    2: "结果合格",
    3: "边界条件满足",
}

ERROR_CODE_MAP = {
    1: "开始",
    2: "车速超限",
    3: "角度过大",
    4: "角度过小",
    5: "目标数异常",
    6: "超时",
    7: "执行成功",
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

    def _send_and_wait(self, send_id, send_data, expect_recv_id, expect_data, timeout):
        """发送CAN消息并等待响应"""
        msg = can.Message(
            arbitration_id=send_id, 
            data=send_data[:64], 
            is_extended_id=False, 
            is_fd=True, 
            dlc=len(send_data)
        )
        self.bus.send(msg)
        self._log(f"[CAL SEND] ID=0x{send_id:03X} DLC={len(send_data)} Data={[hex(b) for b in send_data]}", "SEND")

        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = deadline - time.time()
            recv = self.bus.recv(timeout=min(remaining, 0.1))
            if recv is None:
                continue

            if recv.arbitration_id == expect_recv_id and list(recv.data[:len(expect_data)]) == expect_data:
                self._log(f"[CAL RECV] ID=0x{recv.arbitration_id:03X} Data={[hex(b) for b in recv.data]}", "RECV")
                return recv

        self._log(f"[CAL] 等待响应超时 ID=0x{expect_recv_id:03X}", "ERROR")
        return None

    def static_calibration(self, is_right_radar):
        """静态标定"""
        send_id = self._can_ids['right_static_send'] if is_right_radar else self._can_ids['left_static_send']
        recv_id = self._can_ids['right_static_recv'] if is_right_radar else self._can_ids['left_static_recv']

        radar_name = "右雷达" if is_right_radar else "左雷达"
        self._log(f"[CAL] 开始{radar_name}静态标定...", "INFO")

        resp = self._send_and_wait(send_id, [0x02], recv_id, [0x02, 0x01], CAL_TIMEOUT_STATIC)
        if resp is None:
            self._log(f"[CAL] {radar_name}静态标定启动失败", "ERROR")
            return None

        self._log(f"[CAL] {radar_name}标定已启动，等待标定结果...", "INFO")

        deadline = time.time() + CAL_TIMEOUT_STATIC
        while time.time() < deadline:
            remaining = deadline - time.time()
            recv = self.bus.recv(timeout=min(remaining, 0.1))
            if recv is None:
                continue
            if recv.arbitration_id == recv_id and len(recv.data) >= 2 and recv.data[0] == 0x04:
                self._log(f"[CAL RECV] ID=0x{recv.arbitration_id:03X} Data={[hex(b) for b in recv.data]}", "RECV")
                result = self._parse_cal_result(recv.data[1:])
                return result

        self._log(f"[CAL] {radar_name}标定结果等待超时", "ERROR")
        return None

    def _parse_cal_result(self, data):
        """解析标定结果数据"""
        if len(data) < 20:
            self._log("[CAL] 标定结果数据长度不足", "ERROR")
            return None

        cal_result = struct.unpack('>I', data[0:4])[0]
        process_status = struct.unpack('>I', data[4:8])[0]
        horizontal_raw = struct.unpack('>f', data[8:12])[0]
        vertical_raw = struct.unpack('>f', data[12:16])[0]
        error_code = struct.unpack('>I', data[16:20])[0]

        result = {
            "process_status": process_status,
            "process_status_text": PROCESS_STATUS_MAP.get(process_status, f"未知({process_status})"),
            "cal_result": cal_result,
            "cal_result_text": RESULT_STATUS_MAP.get(cal_result, f"未知({cal_result})"),
            "horizontal_angle": horizontal_raw,
            "vertical_angle": vertical_raw,
            "error_code": error_code,
            "error_code_text": ERROR_CODE_MAP.get(error_code, f"未知({error_code})"),
        }

        self._log(f"[CAL] 标定结果解析:", "OK")
        self._log(f"  标定结果: {result['cal_result_text']}", "OK")
        self._log(f"  进程状态: {result['process_status_text']}", "OK")
        self._log(f"  水平偏差角度: {horizontal_raw:.2f}°", "OK")
        self._log(f"  垂直偏差角度: {vertical_raw:.2f}°", "OK")
        self._log(f"  标定状态: {result['error_code_text']}", "OK")

        return result

    def _read_cal_params(self, is_right_radar):
        section = 'RightRadar' if is_right_radar else 'LeftRadar'
        radar_name = "右雷达" if is_right_radar else "左雷达"

        cfg = configparser.ConfigParser()
        if not os.path.exists(_CAL_CONFIG_PATH):
            self._log(f"[CAL] 配置文件不存在: {_CAL_CONFIG_PATH}", "ERROR")
            return None

        cfg.read(_CAL_CONFIG_PATH, encoding='utf-8')
        if section not in cfg:
            self._log(f"[CAL] 配置文件中未找到 [{section}] 节", "ERROR")
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
            self._log(f"[CAL] 读取{radar_name}标定参数失败: {e}", "ERROR")
            return None

        self._log(f"[CAL] 从配置文件读取{radar_name}参数: "
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

        self._log(f"[CAL] 向{radar_name}下发标定参数...", "INFO")
        resp = self._send_and_wait(send_id, data, recv_id, [0x01, 0x01], CAL_TIMEOUT_PARAM)
        if resp is None:
            self._log(f"[CAL] {radar_name}参数下发失败", "ERROR")
            return False

        self._log(f"[CAL] {radar_name}参数下发成功", "OK")
        return True

    def clear_params(self, is_right_radar):
        """清除标定参数"""
        send_id = self._can_ids['right_param_send'] if is_right_radar else self._can_ids['left_param_send']
        recv_id = self._can_ids['right_param_recv'] if is_right_radar else self._can_ids['left_param_recv']
        radar_name = "右雷达" if is_right_radar else "左雷达"

        self._log(f"[CAL] 清除{radar_name}标定参数...", "INFO")
        resp = self._send_and_wait(send_id, [0x02], recv_id, [0x02, 0x01], CAL_TIMEOUT_PARAM)
        if resp is None:
            self._log(f"[CAL] {radar_name}参数清除失败", "ERROR")
            return False

        self._log(f"[CAL] {radar_name}参数清除成功", "OK")
        return True
