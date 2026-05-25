import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))

import can
import isotp
import time
import threading

from uds.uds_config_tool.ISOStandard.ISOStandard import (
    IsoServices,
    IsoReadDTCSubfunction,
    IsoDiagnosticSessionType,
    RESPONSE_OFFSET,
)

# ============================================================
# ECU 模拟器 - DTC 读取/清除响应
#
# 这个程序模拟一个真实的 ECU，回应 DTC_Test.py 发来的 UDS 请求。
# 它监听 CAN 总线上的诊断请求，根据请求内容构造符合 UDS 标准的响应。
#
# 工作原理：
#   1. DTC_Test.py（诊断仪）向 CAN ID 0x74c 发送请求
#   2. 本模拟器（ECU）从 CAN ID 0x74c 接收请求
#   3. 本模拟器向 CAN ID 0x7cc 发送响应
#   4. DTC_Test.py 从 CAN ID 0x7cc 接收响应
# ============================================================


# ============================================================
# 工具函数：将 3 字节的 DTC 原始数据解析为可读格式
# ============================================================
def format_dtc(dtc_bytes):
    if len(dtc_bytes) < 3:
        return hex(dtc_bytes[0]) if dtc_bytes else "N/A"
    group_map = {0: "P", 1: "C", 2: "B", 3: "U"}
    group = group_map.get((dtc_bytes[0] >> 6) & 0x03, "?")
    first = dtc_bytes[0] & 0x3F
    second = dtc_bytes[1]
    third = dtc_bytes[2]
    return f"{group}{first:02X}{second:02X}{third:02X}"


# ============================================================
# ECU 模拟器类
# 内置一组模拟 DTC，可响应读取和清除请求
# ============================================================
class EcuSimulator:

    # 初始化模拟 DTC 列表
    # 每个 DTC 格式: [3字节代码, 1字节状态]
    SIMULATED_DTCS = [
        [0x03, 0x21, 0x05, 0x28],  # P2105 - Throttle Actuator Control Malfunction (confirmed + testFailed)
        [0x01, 0x23, 0x04, 0x08],  # P2304 - Ignition Coil D Primary/Secondary Circuit (confirmed)
        [0x01, 0x33, 0x01, 0x0A],  # P3301 - Cylinder 1 Misfire (confirmed + testFailedSinceLastClear)
        [0x08, 0x12, 0x03, 0x09],  # B1203 - 车身控制模块故障 (confirmed + testFailed)
    ]

    def __init__(self, canBus, txid=0x7cc, rxid=0x74c):

        self.canBus = canBus
        self.running = False

        # 存储当前模拟 DTC 数据（深拷贝初始列表）
        self.dtc_list = [list(dtc) for dtc in self.SIMULATED_DTCS]

        # ISO-TP 地址配置（与 DTC_Test.py 相反）
        #   ECU 在 0x74c 上收（诊断仪发送），在 0x7cc 上发（诊断仪接收）
        self.address = isotp.Address(
            isotp.AddressingMode.Normal_11bits,
            txid=txid,
            rxid=rxid,
        )

        self.canTp = isotp.CanStack(
            bus=canBus,
            address=self.address,
            params={
                "stmin": 0,
                "blocksize": 8,
                "tx_data_length": 8,
                "tx_data_min_length": 8,
                "tx_padding": 0,
                "rx_flowcontrol_timeout": 5000,
                "rx_consecutive_frame_timeout": 5000,
                "max_frame_size": 8192,
                "can_fd": True,
                "bitrate_switch": True,
                "listen_mode": False,
                "blocking_send": True,
            },
        )

    def start(self):
        self.running = True
        self.canTp.start()
        print("[ECU] Simulator started, waiting for UDS requests ...")
        print(f"[ECU] Listening on RX ID: 0x{self.address.get_rx_arbitration_id():03X}")
        print(f"[ECU] Transmitting on TX ID: 0x{self.address.get_tx_arbitration_id():03X}")

        # 在单独线程中处理请求，主线程可随时停止
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.canTp.stop()
        print("[ECU] Simulator stopped.")

    def _process_loop(self):
        while self.running:
            try:
                # 接收诊断仪发来的 UDS 请求
                request = self.canTp.recv(block=True, timeout=0.5)
                if request is None:
                    continue

                # 解析请求
                self._handle_request(bytearray(request))

            except Exception as e:
                if self.running:
                    print(f"[ECU] Error: {e}")

    def _handle_request(self, request):
        if len(request) < 2:
            return

        service_id = request[0]
        params = request[1:]

        print(f"\n[ECU] <<< Received request: {' '.join(f'{b:02x}' for b in request)}")

        # 根据服务 ID 分发处理
        if service_id == IsoServices.DiagnosticSessionControl:
            self._handle_session_control(params)
        elif service_id == IsoServices.ReadDTCInformation:
            self._handle_read_dtc(params)
        elif service_id == IsoServices.ClearDiagnosticInformation:
            self._handle_clear_dtc(params)
        else:
            # 不支持的请求，返回否定响应（0x7F + 服务ID + NRC=0x11=serviceNotSupported）
            nrc_response = bytearray([0x7F, service_id, 0x11])
            print(f"[ECU] >>> Unsupported service 0x{service_id:02X}, sending NRC")
            self.canTp.send(nrc_response)

    # ============================================================
    # 处理诊断会话控制请求 (0x10)
    # 响应格式: [0x50, subfunction]
    # ============================================================
    def _handle_session_control(self, params):
        if len(params) < 1:
            return

        subfunction = params[0]
        # 正响应: 服务ID + 0x40 = 0x50
        response = bytearray([0x50, subfunction])
        print(f"[ECU] >>> DiagnosticSessionControl -> session=0x{subfunction:02X}")
        self.canTp.send(response)

    # ============================================================
    # 处理读取 DTC 请求 (0x19)
    # 支持的子功能:
    #   0x01 = reportNumberOfDTCByStatusMask - 返回 DTC 数量
    #   0x02 = reportDTCByStatusMask - 返回 DTC 详细信息
    # ============================================================
    def _handle_read_dtc(self, params):
        if len(params) < 1:
            return

        subfunction = params[0]
        print(f"[ECU] >>> ReadDTCInformation subfunction=0x{subfunction:02X}")

        # 按状态掩码过滤 DTC（如果提供了状态掩码）
        status_mask = params[1] if len(params) > 1 else 0xFF
        filtered_dtcs = [dtc for dtc in self.dtc_list if (dtc[3] & status_mask)]

        if subfunction == IsoReadDTCSubfunction.reportNumberOfDTCByStatusMask:
            # 响应: [0x59, 0x01, statusAvailability, dtcFormat, countH, countL]
            status_avail = 0xFF  # 所有状态位都可用
            dtc_format = 0x00    # ISO 15031-6 格式
            count = len(filtered_dtcs)
            response = bytearray([0x59, 0x01, status_avail, dtc_format,
                                  (count >> 8) & 0xFF, count & 0xFF])
            print(f"[ECU] >>> DTC count = {count}")

        elif subfunction == IsoReadDTCSubfunction.reportDTCByStatusMask:
            # 响应: [0x59, 0x02, statusAvailability, dtcFormat, countH, countL,
            #        dtc1_3bytes, status1, dtc2_3bytes, status2, ...]
            status_avail = 0xFF
            dtc_format = 0x00
            count = len(filtered_dtcs)
            response = bytearray([0x59, 0x02, status_avail, dtc_format,
                                  (count >> 8) & 0xFF, count & 0xFF])
            for dtc in filtered_dtcs:
                response.extend([dtc[0], dtc[1], dtc[2], dtc[3]])
            print(f"[ECU] >>> DTC details: {count} DTC(s)")
            for dtc in filtered_dtcs:
                print(f"       {format_dtc(dtc[:3])}  status=0x{dtc[3]:02X}")

        elif subfunction == IsoReadDTCSubfunction.reportSupportedDTC:
            # 返回所有支持的 DTC（已存储的和未存储的）
            # 这里简单返回已存储的 DTC
            status_avail = 0xFF
            dtc_format = 0x00
            count = len(self.dtc_list)
            response = bytearray([0x59, 0x0A, status_avail, dtc_format,
                                  (count >> 8) & 0xFF, count & 0xFF])
            for dtc in self.dtc_list:
                response.extend([dtc[0], dtc[1], dtc[2], dtc[3]])

        else:
            # 不支持的子功能 -> 否定响应
            nrc = bytearray([0x7F, 0x19, 0x12])  # 0x12 = subFunctionNotSupported
            print(f"[ECU] >>> Subfunction 0x{subfunction:02X} not supported")
            self.canTp.send(nrc)
            return

        self.canTp.send(response)

    # ============================================================
    # 处理清除 DTC 请求 (0x14)
    # 请求格式: [0x14, groupH, groupM, groupL]
    # 响应格式: [0x54]
    # ============================================================
    def _handle_clear_dtc(self, params):
        if len(params) < 3:
            return

        group = (params[0] << 16) | (params[1] << 8) | params[2]
        print(f"[ECU] >>> ClearDiagnosticInformation group=0x{group:06X}")

        if group == 0xFFFFFF:
            # 清除所有 DTC
            cleared_count = len(self.dtc_list)
            self.dtc_list.clear()
            print(f"[ECU] >>> Cleared all {cleared_count} DTC(s)")
        else:
            # 按组别清除（这里简化处理，只保留不匹配组别的 DTC）
            target_group = (group >> 16) & 0xFF
            remaining = []
            for dtc in self.dtc_list:
                if (dtc[0] >> 6) & 0x03 != target_group:
                    remaining.append(dtc)
            cleared_count = len(self.dtc_list) - len(remaining)
            self.dtc_list = remaining
            print(f"[ECU] >>> Cleared {cleared_count} DTC(s) in group 0x{target_group:02X}")

        # 正响应: [0x54]
        response = bytearray([0x54])
        self.canTp.send(response)
        print(f"[ECU] >>> Remaining DTCs: {len(self.dtc_list)}")


# ============================================================
# 主程序：启动 ECU 模拟器
# 按 Ctrl+C 停止
# ============================================================
if __name__ == "__main__":

    canBus = can.interface.Bus(
        interface="kvaser",
        channel="1",
        bitrate=500000,
        data_bitrate=2000000,
        fd=True,
    )

    try:
        # 创建并启动 ECU 模拟器
        # CAN ID 与 DTC_Test.py 相反:
        #   DTC_Test.py: txid=0x74c（发）, rxid=0x7cc（收）
        #   本模拟器:    txid=0x7cc（发）, rxid=0x74c（收）
        ecu = EcuSimulator(canBus, txid=0x7cc, rxid=0x74c)
        ecu.start()

        # 保持主线程运行，等待 Ctrl+C
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[ECU] Shutting down ...")
    finally:
        ecu.stop()
        canBus.shutdown()
