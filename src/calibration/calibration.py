# -*- coding: utf-8 -*-
import sys
import os
import time
import struct
import threading

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'lib'))

import can


CAL_TIMEOUT_STATIC = 10.0
CAL_TIMEOUT_PARAM = 3.0

LEFT_STATIC_SEND_ID = 0x61
LEFT_STATIC_RECV_ID = 0x71
RIGHT_STATIC_SEND_ID = 0x261
RIGHT_STATIC_RECV_ID = 0x271

LEFT_PARAM_SEND_ID = 0x60
LEFT_PARAM_RECV_ID = 0x70
RIGHT_PARAM_SEND_ID = 0x260
RIGHT_PARAM_RECV_ID = 0x270

PARAM_STRUCT = struct.Struct('>fffffffB')

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
    2: "停止",
    3: "未完成",
    4: "车速超限",
    5: "角度过大",
    6: "角度过小",
    7: "目标数异常",
    8: "超时",
    9: "执行成功",
}


class CalibrationManager:
    def __init__(self, channel, bitrate, data_bitrate, log_callback=None):
        self.channel = channel
        self.bitrate = int(bitrate)
        self.data_bitrate = int(data_bitrate)
        self.log_callback = log_callback
        self.bus = None
        self._running = False

    def _log(self, msg, tag="INFO"):
        print(msg)
        if self.log_callback:
            self.log_callback(msg, tag)

    def connect(self):
        self.bus = can.interface.Bus(
            interface="kvaser",
            channel=self.channel,
            bitrate=self.bitrate,
            data_bitrate=self.data_bitrate,
            fd=True,
        )
        self._log(f"[CAL] CAN 总线已连接 channel={self.channel} bitrate={self.bitrate} data_bitrate={self.data_bitrate}", "OK")

    def disconnect(self):
        if self.bus:
            self.bus.shutdown()
            self.bus = None
            self._log("[CAL] CAN 总线已断开", "INFO")

    def _send_and_wait(self, send_id, send_data, expect_recv_id, expect_data, timeout):
        msg = can.Message(arbitration_id=send_id, data=send_data[:64], is_extended_id=False, is_fd=True, dlc=len(send_data))
        self.bus.send(msg)
        self._log(f"[CAL SEND] ID=0x{send_id:03X} DLC={len(send_data)} Data={[hex(b) for b in send_data]}", "SEND")

        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = deadline - time.time()
            recv = self.bus.recv(timeout=min(remaining, 0.1))
            if recv is None:
                continue
            self._log(f"[CAL RECV] ID=0x{recv.arbitration_id:03X} Data={[hex(b) for b in recv.data]}", "RECV")

            if recv.arbitration_id == expect_recv_id and list(recv.data[:len(expect_data)]) == expect_data:
                return recv

        self._log(f"[CAL] 等待响应超时 ID=0x{expect_recv_id:03X}", "ERROR")
        return None

    def static_calibration(self, is_right_radar):
        send_id = RIGHT_STATIC_SEND_ID if is_right_radar else LEFT_STATIC_SEND_ID
        recv_id = RIGHT_STATIC_RECV_ID if is_right_radar else LEFT_STATIC_RECV_ID

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
            self._log(f"[CAL RECV] ID=0x{recv.arbitration_id:03X} Data={[hex(b) for b in recv.data]}", "RECV")
            if recv.arbitration_id == recv_id and len(recv.data) >= 2 and recv.data[0] == 0x04:
                result = self._parse_cal_result(recv.data[1:])
                return result

        self._log(f"[CAL] {radar_name}标定结果等待超时", "ERROR")
        return None

    def _parse_cal_result(self, data):
        if len(data) < 8:
            self._log("[CAL] 标定结果数据长度不足", "ERROR")
            return None

        cal_result = (data[0] >> 4) & 0x0F
        process_status = (data[1] >> 4) & 0x0F
        horizontal_raw = int.from_bytes(data[2:4], byteorder='big', signed=True)
        vertical_raw = int.from_bytes(data[4:6], byteorder='big', signed=True)
        error_code = data[6]

        horizontal_angle = horizontal_raw * 0.01
        vertical_angle = vertical_raw * 0.01

        result = {
            "process_status": process_status,
            "process_status_text": PROCESS_STATUS_MAP.get(process_status, f"未知({process_status})"),
            "cal_result": cal_result,
            "cal_result_text": RESULT_STATUS_MAP.get(cal_result, f"未知({cal_result})"),
            "horizontal_angle": horizontal_angle,
            "vertical_angle": vertical_angle,
            "error_code": error_code,
            "error_code_text": ERROR_CODE_MAP.get(error_code, f"未知({error_code})"),
        }

        self._log(f"[CAL] 标定结果解析:", "OK")
        self._log(f"  进程状态: {result['process_status_text']}", "OK")
        self._log(f"  标定结果: {result['cal_result_text']}", "OK")
        self._log(f"  水平偏差角度: {horizontal_angle:.2f}°", "OK")
        self._log(f"  垂直偏差角度: {vertical_angle:.2f}°", "OK")
        self._log(f"  错误码: {result['error_code_text']}", "OK")

        return result

    def send_params(self, is_right_radar, vehicle_height,
                    x_offset, y_offset, z_offset,
                    yaw_angle, pitch_angle, roll_angle, orientation):
        send_id = RIGHT_PARAM_SEND_ID if is_right_radar else LEFT_PARAM_SEND_ID
        recv_id = RIGHT_PARAM_RECV_ID if is_right_radar else LEFT_PARAM_RECV_ID
        radar_name = "右雷达" if is_right_radar else "左雷达"

        packed = PARAM_STRUCT.pack(vehicle_height,
                                   x_offset, y_offset, z_offset,
                                   yaw_angle, pitch_angle, roll_angle,
                                   orientation)
        data = [0x01] + list(packed) + [0x00] * 34

        self._log(f"[CAL] 向{radar_name}下发标定参数...", "INFO")
        resp = self._send_and_wait(send_id, data, recv_id, [0x01, 0x01], CAL_TIMEOUT_PARAM)
        if resp is None:
            self._log(f"[CAL] {radar_name}参数下发失败", "ERROR")
            return False

        self._log(f"[CAL] {radar_name}参数下发成功", "OK")
        return True

    def clear_params(self, is_right_radar):
        send_id = RIGHT_PARAM_SEND_ID if is_right_radar else LEFT_PARAM_SEND_ID
        recv_id = RIGHT_PARAM_RECV_ID if is_right_radar else LEFT_PARAM_RECV_ID
        radar_name = "右雷达" if is_right_radar else "左雷达"

        self._log(f"[CAL] 清除{radar_name}标定参数...", "INFO")
        resp = self._send_and_wait(send_id, [0x02], recv_id, [0x02, 0x01], CAL_TIMEOUT_PARAM)
        if resp is None:
            self._log(f"[CAL] {radar_name}参数清除失败", "ERROR")
            return False

        self._log(f"[CAL] {radar_name}参数清除成功", "OK")
        return True
