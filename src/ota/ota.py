import sys
import os
if getattr(sys, 'frozen', False):
    _BASE_DIR = sys._MEIPASS
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_BASE_DIR, 'lib'))

import can
import isotp
from uds import UdsMessage, IsoServices, Uds
import time
import threading
import zlib
from intelhex import IntelHex


# ISO-TP 参数配置
ISOTP_PARAMS = {
    "stmin": 0,
    "override_receiver_stmin": 0.0001,
    "blocksize": 8,
    "wftmax": 0,
    "tx_data_length": 8,
    "tx_data_min_length": 8,
    "tx_padding": 0,
    "rx_flowcontrol_timeout": 5000,
    "rx_consecutive_frame_timeout": 5000,
    "max_frame_size": 8192,
    "can_fd": True,
    "bitrate_switch": True,
    "rate_limit_enable": False,
    "rate_limit_max_bitrate": 1000000,
    "rate_limit_window_size": 0.2,
    "listen_mode": False,
    "blocking_send": True,
}

# 安全帧 CAN ID 和数据
FORCEJUMP_CAN_ID = 0x190C8532
FORCEJUMP_DATA = [0x02, 0x10, 0x60,
                  0x46, 0x4F, 0x52, 0x43, 0x45, 0x4A, 0x55, 0x4D, 0x50,  # "FORCEJUMP"
                  0xA5, 0xB6, 0xC7, 0xD8]

# 固件起始地址和文件路径（根据实际情况修改）
FLASH_START_ADDR = 0x00090000
FLASH_ERASE_SIZE = 0x2000
HEX_FILE_PATH = "data.hex"


def uds_send(canUds, service, params, confirm=None, timeout=2.0):
    """发送 UDS 请求并等待正响应"""
    msg = UdsMessage()
    msg.create(service, params)
    res, resp = canUds.send(msg, timeout=timeout, confirm=confirm)
    if not res:
        raise Exception(f"UDS 请求失败: service=0x{service:02X}, params={[hex(p) for p in params]}")
    return resp


def step_a1_extended_session(canUds):
    """A1: 切换到扩展会话"""
    uds_send(canUds, IsoServices.DiagnosticSessionControl, [0x03],
             confirm=[ 0x03], timeout=2.0)
    print("[A1] 扩展会话切换成功")


def step_a2_ecu_reset(canUds):
    """A2: ECU 复位"""
    uds_send(canUds, IsoServices.EcuReset, [0x01],
             confirm=[ 0x01], timeout=2.0)
    print("[A2] ECU 复位已发送")


def step_a3_forcejump(canBus):
    """A3: 发送 FORCEJUMP 安全帧，使 ECU 停留在 PFBoot"""
    force_msg = can.Message(
        arbitration_id=FORCEJUMP_CAN_ID,
        data=FORCEJUMP_DATA,
        is_extended_id=True,
        bitrate_switch=True,
        is_fd=True,
    )
    for _ in range(20): #20×0.1=2s，确保安全帧被正确接收，考虑发送也需要时间，实际持续3s左右
        canBus.send(force_msg)
        time.sleep(0.1)
    print("[A3] FORCEJUMP 安全帧发送完成（持续 3s）")


def step_b_tester_present(canUds, stop_event):
    """B: 后台线程，每 1s 发送一次 TesterPresent 维持扩展会话"""
    msg = UdsMessage()
    msg.create(IsoServices.TesterPresent, [0x80])
    while not stop_event.is_set():
        canUds.send(msg, responseRequired=False, timeout=0.5)
        time.sleep(1.0)


def step_c_erase(canUds, address, length):
    """C: 擦除目标区域"""
    addr_bytes = list(address.to_bytes(4, 'big'))
    len_bytes = list(length.to_bytes(4, 'big'))
    params = [0x01, 0xFF, 0x00, 0x00] + addr_bytes + len_bytes
    uds_send(canUds, IsoServices.RoutineControl, params,
             confirm=[ 0x01, 0xFF, 0x00], timeout=30.0)
    print(f"[C] 擦除完成 address=0x{address:08X} length={length}")


def step_d1_request_download(canUds, address, length):
    """D1: 请求下载"""
    addr_bytes = list(address.to_bytes(4, 'big'))
    len_bytes = list(length.to_bytes(4, 'big'))
    params = [0x00, 0x44] + addr_bytes + len_bytes
    resp = uds_send(canUds, IsoServices.RequestDownload, params,
                    confirm=[], timeout=5.0)
    max_block = (resp.frame[2] << 8) | resp.frame[3]
    print(f"[D1] 请求下载成功 MaxBlock={max_block}")
    return max_block


def step_d2_transfer_data(canUds, file_data, chunk_size):
    """D2: 传输数据块"""
    total_len = len(file_data)
    block_count = 0
    for offset in range(0, total_len, chunk_size):
        block = file_data[offset:offset + chunk_size]
        sn = (block_count + 1) & 0xFF
        msg = UdsMessage()
        msg.create(IsoServices.TransferData, [sn] + list(block))
        uds_send(canUds, IsoServices.TransferData, [sn] + list(block),
                 confirm=[ sn], timeout=5.0)
        block_count += 1
        if block_count % 10 == 0 or offset + chunk_size >= total_len:
            print(f"[D2] 传输进度: {min(offset + chunk_size, total_len)}/{total_len}")
    print(f"[D2] 数据传输完成 共 {block_count} 块")


def step_d3_transfer_exit(canUds):
    """D3: 传输结束"""
    uds_send(canUds, IsoServices.RequestTransferExit, [],
             confirm=[], timeout=5.0)
    print("[D3] 传输结束")


def step_e1_crc32_check(canUds, file_data):
    """E1: CRC32 校验"""
    crc = zlib.crc32(file_data) & 0xFFFFFFFF
    crc_bytes = list(crc.to_bytes(4, 'big'))
    params = [0x01, 0x02, 0x12] + crc_bytes
    uds_send(canUds, IsoServices.RoutineControl, params,
             confirm=[ 0x01, 0x02, 0x12], timeout=30.0)
    print(f"[E1] CRC32 校验通过 crc=0x{crc:08X}")


def step_e2_dependency_check(canUds):
    """E2: 依赖检查"""
    uds_send(canUds, IsoServices.RoutineControl, [0x01, 0x02, 0x05],
             confirm=[ 0x01, 0x02, 0x05], timeout=10.0)
    print("[E2] 依赖检查通过")


def step_e3_ecu_reset(canUds):
    """E3: ECU 复位，启动新固件"""
    uds_send(canUds, IsoServices.EcuReset, [0x01],
             confirm=[ 0x01], timeout=2.0)
    print("[E3] ECU 复位已发送，新固件即将启动")


def main():
    # 初始化 CAN 总线
    canBus = can.interface.Bus(
        interface="kvaser",
        channel="0",
        bitrate=500000,
        data_bitrate=2000000,
        fd=True,
    )

    try:
        # 初始化 ISO-TP 传输层
        canTp = isotp.CanStack(
            bus=canBus,
            address=isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x74C, rxid=0x7CC),
            params=ISOTP_PARAMS,
        )
        canTp.start()

        canUds = Uds(canTp)

        with open(HEX_FILE_PATH, "rb") as f:
            file_data = f.read()
        flash_size = len(file_data)
        #读取Hex文件
        ihObj = IntelHex(HEX_FILE_PATH)
        segments = ihObj.segments()

        file_size = segments[0][1] - segments[0][0]
        file_data =  bytes(ihObj.tobinarray(start=segments[0][0], end=segments[0][1] - 1))
        start_address = segments[0][0]
        #文件大小
        file_size_bytes = file_size.to_bytes(4, byteorder='big')
        #起始地址
        start_address_bytes = start_address.to_bytes(4, byteorder='big')


        # ---- A: 进入 PFBoot OTA 模式 ----
        step_a1_extended_session(canUds)
        time.sleep(0.1)

        step_a2_ecu_reset(canUds)  # ECU 复位

        step_a3_forcejump(canBus)  # 发送 FORCEJUMP 安全帧

        # 等待 PFBoot 启动
        time.sleep(0.5)

        # ---- B: 维持扩展会话 ----
        canUds = Uds(canTp)  # 重新初始化 Uds（ECU 复位后重新建立连接）
        step_a1_extended_session(canUds)

        tp_stop = threading.Event()
        tp_thread = threading.Thread(target=step_b_tester_present, args=(canUds, tp_stop), daemon=True)
        tp_thread.start()
        time.sleep(0.1)

        # ---- C: 擦除目标区域 ----
        step_c_erase(canUds, FLASH_START_ADDR, FLASH_ERASE_SIZE)

        # ---- D: 下载与传输 ----
        max_block = step_d1_request_download(canUds, start_address_bytes, file_size_bytes)

        # 根据 MaxBlock 使用合适的块大小（留出序列号+服务ID的头部空间）
        chunk_size = min(max_block - 2, 4094)
        step_d2_transfer_data(canUds, file_data, chunk_size)

        step_d3_transfer_exit(canUds)

        # ---- E: 完整性校验与激活 ----
        step_e1_crc32_check(canUds, file_data)

        step_e2_dependency_check(canUds)

        # 停止 TesterPresent 线程
        tp_stop.set()
        tp_thread.join(timeout=2.0)

        step_e3_ecu_reset(canUds)

        print("\nOTA 升级完成！")

    finally:
        canBus.shutdown()


if __name__ == "__main__":
    main()
