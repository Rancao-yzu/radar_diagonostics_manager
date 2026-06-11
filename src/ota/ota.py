import sys
import os
if getattr(sys, 'frozen', False):
    _BASE_DIR = sys._MEIPASS
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_BASE_DIR, 'lib'))

import can
import isotp
from uds import UdsMessage, IsoServices, Uds
import time
import threading
import zlib
from intelhex import IntelHex
import ctypes


# ISO-TP 参数配置
ISOTP_PARAMS = {
    "stmin": 0,
    "override_receiver_stmin": 0.0001,
    "blocksize": 8,
    "wftmax": 0,
    "tx_data_length": 64,
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

# 安全帧 CAN ID 和数据 (FORCEJUMP)
FORCEJUMP_CAN_ID = 0x190C8532
FORCEJUMP_DATA = [0x02, 0x10, 0x60,
                  0x46, 0x4F, 0x52, 0x43, 0x45, 0x4A, 0x55, 0x4D, 0x50,  # "FORCEJUMP"
                  0xA5, 0xB6, 0xC7, 0xD8]

# hex文件路径 (基于项目根目录)
HEX_FILE_PATH = os.path.join(_BASE_DIR, "90", "1M_CUSTOMER_APP烧录_fffash", "productionsw.hex")

# 安全访问 DLL 路径 (基于项目根目录)
SECURITY_DLL_PATH = os.path.join(_BASE_DIR, "90", "1M_CUSTOMER_APP烧录_fffash",
                                  "security_dll", "SeednKey.dll")


def uds_send(canUds, service, params, confirm=None, timeout=2.0):
    """发送 UDS 请求并检查正响应"""
    msg = UdsMessage()
    msg.create(service, params)
    res, resp = canUds.send(msg, timeout=timeout, confirm=confirm)
    if not res:
        raise Exception(f"UDS 请求失败: service=0x{service:02X}, params={[hex(p) for p in params]}")
    return resp


def seed_key_func(dll_path, seed, seed_level):
    """
    安全访问种子-密钥计算，通过 ctypes 调用 GenerateKeyEx。
    :param dll_path: DLL路径
    :param seed: ECU返回的种子 (byte list)
    :param seed_level: 安全访问等级
    :return: 计算出的密钥 (byte list)
    """
    # 将DLL所在目录加入PATH，确保其依赖DLL能被找到
    path = os.environ.get("PATH", "")
    dll_dir = os.path.dirname(os.path.abspath(dll_path))
    if dll_dir not in path:
        os.environ["PATH"] = dll_dir + os.pathsep + path

    if not os.path.exists(dll_path):
        raise FileNotFoundError(f"DLL not found at {dll_path}")

    print(f"  Loading DLL: {dll_path}")
    dll = ctypes.CDLL(dll_path)

    # GenerateKeyEx 签名
    generateKeyEx = dll.GenerateKeyEx
    generateKeyEx.restype = ctypes.c_int
    generateKeyEx.argtypes = [
        ctypes.POINTER(ctypes.c_ubyte),  # ipSeedArray
        ctypes.c_uint,                   # iSeedArraySize
        ctypes.c_uint,                   # iSecurityLevel
        ctypes.c_char_p,                 # ipVariant
        ctypes.POINTER(ctypes.c_ubyte),  # iopKeyArray
        ctypes.c_uint,                   # iMaxKeyArraySize
        ctypes.POINTER(ctypes.c_uint)    # oActualKeyArraySize
    ]

    seed_bytes = bytes(seed)
    seed_array = (ctypes.c_ubyte * len(seed_bytes))(*seed_bytes)
    variant = b"VARIANT_A"
    max_key_size = 5000
    key_array = (ctypes.c_ubyte * max_key_size)()
    actual_key_size = ctypes.c_uint(0)

    print(f"  Seed level: 0x{seed_level:02X}, Seed: {[format(s, '02x') for s in seed]}")

    result = generateKeyEx(
        seed_array,
        len(seed_bytes),
        seed_level,
        variant,
        key_array,
        max_key_size,
        ctypes.byref(actual_key_size)
    )
    if result != 0:
        raise Exception(f"GenerateKeyEx failed with error code: {result}")

    key_data = bytes(key_array).rstrip(b'\x00')
    key_list = list(key_data)
    print(f"  Key: {[format(k, '02x') for k in key_list]}")
    return key_list


# ======================== 流程步骤 ========================

def step_sending_security_frame(canBus):
    """Sending_SecurityFrame: 发送 FORCEJUMP 安全帧 100次，周期50ms"""
    force_msg = can.Message(
        arbitration_id=FORCEJUMP_CAN_ID,
        data=FORCEJUMP_DATA,
        is_extended_id=True,
        bitrate_switch=True,
        is_fd=True,
    )
    for _ in range(100):
        canBus.send(force_msg)
        time.sleep(0.05)
    print("[Sending_SecurityFrame] 安全帧发送完成 (100次)") 


def step_load_file():
    """LoadFile: 加载 hex 文件，返回 (data, address, length, crc)"""
    ihObj = IntelHex(HEX_FILE_PATH)
    segments = ihObj.segments()
    start = segments[0][0]
    end = segments[0][1]
    file_data = bytes(ihObj.tobinarray(start=start, end=end - 1))
    file_length = end - start
    file_crc = zlib.crc32(file_data) & 0xFFFFFFFF

    print(f"[LoadFile] {HEX_FILE_PATH}")
    print(f"  Address: 0x{start:08X}, Length: 0x{file_length:08X} ({file_length}), CRC32: 0x{file_crc:08X}")
    return start, file_data, file_length, file_crc


def step1_extended_session(canUds):
    """step1: 扩展会话 10 03 -> 50 03"""
    uds_send(canUds, IsoServices.DiagnosticSessionControl, [0x03],
             confirm=[0x03], timeout=3.0)
    print("[step1_extendedsession] 扩展会话切换成功")


def step2_programming_session(canUds):
    """step2: 编程会话 10 06 -> 50 06"""
    uds_send(canUds, IsoServices.DiagnosticSessionControl, [0x06],
             confirm=[0x06], timeout=3.0)
    print("[step2_programsession] 编程会话切换成功")


def step3_security_access(canUds):
    """step3: 安全访问, level 0x61"""
    res, response = canUds.sercurityAccess(
        seedLevel=0x61,
        dllPath=SECURITY_DLL_PATH,
        seedFunc=seed_key_func,
        printLog=True
    )
    if not res:
        raise Exception("step3_securityseed 安全访问失败")
    print("[step3_securityseed] 安全访问通过")


def step5_erase_block(canUds, address, length):
    """step5: 擦除块 31 01 FF 00 + address + length"""
    addr_bytes = list(address.to_bytes(4, 'big'))
    len_bytes = list(length.to_bytes(4, 'big'))
    params = [0x01, 0xFF, 0x00] + addr_bytes + len_bytes
    uds_send(canUds, IsoServices.RoutineControl, params,
             confirm=[0x01, 0xFF, 0x00, 0x10], timeout=20.0)
    print(f"[step5_eraseblock_APP] 擦除完成 address=0x{address:08X} length={length}")


def step10_request_download(canUds, address, length):
    """step10: 请求下载 34 00 44 + address + length -> 74 20"""
    addr_bytes = list(address.to_bytes(4, 'big'))
    len_bytes = list(length.to_bytes(4, 'big'))
    params = [0x00, 0x44] + addr_bytes + len_bytes
    uds_send(canUds, IsoServices.RequestDownload, params,
             confirm=[0x20], timeout=5.0)
    print("[step10_RequestDownload] 请求下载成功")


def step11_transfer_data(canUds, file_data):
    """step11: 传输数据 TRANSFILE, chunkSize=4093"""
    canUds.transferFile(fileData=file_data, chunkSize=4093)
    total_blocks = len(file_data) // 4093 + (1 if len(file_data) % 4093 else 0)
    print(f"[step11_transferdata0] 数据传输完成 共 {total_blocks} 块")


def step12_transfer_exit(canUds):
    """step12: 传输结束 37 -> 77"""
    uds_send(canUds, IsoServices.RequestTransferExit, [],
             confirm=[], timeout=5.0)
    print("[step12_RequestTransferExit0] 传输结束")


def step13_crc_check(canUds, crc):
    """step13: CRC校验 31 01 02 12 + crc -> 71 01 02 12 10 00"""
    crc_bytes = list(crc.to_bytes(4, 'big'))
    params = [0x01, 0x02, 0x12] + crc_bytes
    uds_send(canUds, IsoServices.RoutineControl, params,
             confirm=[0x01, 0x02, 0x12, 0x10, 0x00], timeout=5.0)
    print(f"[step13_CRC] CRC校验通过 crc=0x{crc:08X}")


def step14_write_cust_flag(canUds):
    """step14: 写客户标志 2E FC 01 43 55 41 50 -> 6E FC 01"""
    uds_send(canUds, IsoServices.WriteDataByIdentifier,
             [0xFC, 0x01, 0x43, 0x55, 0x41, 0x50],  # "CUAP" = Customer App
             confirm=[0xFC, 0x01], timeout=3.2)
    print("[step14_write_cust_flag] 客户标志写入成功")


def step19_check_dependencies(canUds):
    """step19: 依赖检查 31 01 02 05"""
    uds_send(canUds, IsoServices.RoutineControl, [0x01, 0x02, 0x05],
             confirm=[], timeout=3.1)
    print("[step19_Check_dependencies] 依赖检查通过")


def step20_ecu_reset(canUds):
    """step20: ECU复位到默认会话 10 01"""
    uds_send(canUds, IsoServices.DiagnosticSessionControl, [0x01],
             confirm=[], timeout=8.0)
    print("[step20_ecuReset] ECU复位已发送")


# ======================== 主流程 ========================

def main():
    canBus = can.interface.Bus(
        interface="kvaser",
        channel="0",
        bitrate=500000,
        data_bitrate=2000000,
        fd=True,
    )

    try:
        # ---- Sending_SecurityFrame: 发送 FORCEJUMP 安全帧 ----
        step_sending_security_frame(canBus)

        # ---- 初始化 ISO-TP ----
        canTp = isotp.CanStack(
            bus=canBus,
            address=isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x74C, rxid=0x7CC),
            params=ISOTP_PARAMS,
        )
        canTp.start()

        canUds = Uds(canTp)

        # ---- LoadFile: 加载 hex 文件 ----
        start_address, file_data, file_length, file_crc = step_load_file()

        # ---- step1: 扩展会话 ----
        step1_extended_session(canUds)

        # ---- step2: 编程会话 ----
        step2_programming_session(canUds)

        # ---- step3: 安全访问 ----
        step3_security_access(canUds)

        # ---- step5: 擦除 ----
        step5_erase_block(canUds, start_address, file_length)

        # ---- step10: 请求下载 ----
        step10_request_download(canUds, start_address, file_length)

        # ---- step11: 传输数据 ----
        step11_transfer_data(canUds, file_data)

        # ---- step12: 传输结束 ----
        step12_transfer_exit(canUds)

        # ---- step13: CRC校验 ----
        step13_crc_check(canUds, file_crc)

        # ---- step14: 写客户标志 ----
        step14_write_cust_flag(canUds)

        # ---- step19: 依赖检查 ----
        step19_check_dependencies(canUds)

        # ---- step20: ECU复位 ----
        step20_ecu_reset(canUds)

        print("\nOTA 升级完成！")

    finally:
        canBus.shutdown()


if __name__ == "__main__":
    main()



