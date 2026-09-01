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
import zlib
from intelhex import IntelHex


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


# 日志输出函数：默认 print，run_ota 启动时替换为 GUI 日志回调，结束后还原
_log_fn = print


def _log(msg, tag="INFO"):
    _log_fn(msg,tag)


def uds_send(canUds, service, params, confirm=None, timeout=2.0):
    """发送 UDS 请求并检查正响应"""
    msg = UdsMessage()
    msg.create(service, params)
    _log(f"  [TX] {[format(b, '02X') for b in msg.frame]}", "SEND")
    res, resp = canUds.send(msg, timeout=timeout, confirm=confirm)
    # 调试: 打印原始响应帧; resp 为数字时是库内部错误码(2=超时 3=响应不匹配 4=异常)
    if resp is not None and hasattr(resp, 'frame') and len(resp.frame) > 0:
        _log(f"  [RX] {[format(b, '02X') for b in resp.frame]}", "RECV")
    if not res:
        if not (resp is not None and hasattr(resp, 'frame')):
            _log(f"  [RX] 无响应 (库错误码: {resp})", "ERROR")
        raise Exception(f"UDS 请求失败: service=0x{service:02X}, params={[hex(p) for p in params]}")
    return resp


def seed_key_func(dll_path, seed, seed_level):
    """
    安全访问种子-密钥计算（Linux 纯 Python 实现，替代 Windows SeednKey.dll）。
    按 docx/Security.md 对 DLL 行为的拆解：密钥为固定 2000 字节 0x11，与种子内容无关。
    :param dll_path: 未使用（保留参数以兼容 Uds.sercurityAccess 的调用签名）
    :param seed: ECU返回的种子 (byte list)
    :param seed_level: 安全访问等级
    :return: 计算出的密钥 (byte list)
    """
    _log(f"  Seed level: 0x{seed_level:02X}, Seed({len(seed)}B): {[format(s, '02x') for s in seed[:8]]} ...")
    key_list = [0x11] * 2000
    _log(f"  Key: {len(key_list)} bytes of 0x11")
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
    _log("[Sending_SecurityFrame] 安全帧发送完成 (100次)") 


def step_load_file(hex_path):
    """LoadFile: 加载 hex 文件，返回 (data, address, length, crc)"""
    ihObj = IntelHex(hex_path)
    segments = ihObj.segments()
    start = segments[0][0]
    end = segments[0][1]
    file_data = bytes(ihObj.tobinarray(start=start, end=end - 1))
    file_length = end - start
    file_crc = zlib.crc32(file_data) & 0xFFFFFFFF

    _log(f"[LoadFile] {hex_path}")
    _log(f"  Address: 0x{start:08X}, Length: 0x{file_length:08X} ({file_length}), CRC32: 0x{file_crc:08X}")
    return start, file_data, file_length, file_crc


def step1_extended_session(canUds):
    """step1: 扩展会话 10 03 -> 50 03"""
    uds_send(canUds, IsoServices.DiagnosticSessionControl, [0x03],
             confirm=[0x03], timeout=3.0)
    _log("[step1_extendedsession] 扩展会话切换成功")


def step2_programming_session(canUds):
    """step2: 编程会话 10 06 -> 50 06"""
    uds_send(canUds, IsoServices.DiagnosticSessionControl, [0x06],
             confirm=[0x06], timeout=3.0)
    _log("[step2_programsession] 编程会话切换成功")


def step3_security_access(canUds):
    """step3: 安全访问, level 0x61（密钥由 seed_key_func 纯 Python 计算，无需 DLL）"""
    res, response = canUds.sercurityAccess(
        seedLevel=0x61,
        dllPath=None,  # Linux 下无 DLL，仅为兼容接口签名传 None
        seedFunc=seed_key_func,
        printLog=False
    )
    if not res:
        raise Exception("step3_securityseed 安全访问失败")
    _log("[step3_securityseed] 安全访问通过")


def step5_erase_block(canUds, address, length):
    """step5: 擦除块 31 01 FF 00 + address + length"""
    addr_bytes = list(address.to_bytes(4, 'big'))
    len_bytes = list(length.to_bytes(4, 'big'))
    params = [0x01, 0xFF, 0x00] + addr_bytes + len_bytes
    uds_send(canUds, IsoServices.RoutineControl, params,
             confirm=[0x01, 0xFF, 0x00, 0x10], timeout=20.0)
    _log(f"[step5_eraseblock_APP] 擦除完成 address=0x{address:08X} length={length}")


def step10_request_download(canUds, address, length):
    """step10: 请求下载 34 00 44 + address + length -> 74 20"""
    addr_bytes = list(address.to_bytes(4, 'big'))
    len_bytes = list(length.to_bytes(4, 'big'))
    params = [0x00, 0x44] + addr_bytes + len_bytes
    uds_send(canUds, IsoServices.RequestDownload, params,
             confirm=[0x20], timeout=5.0)
    _log("[step10_RequestDownload] 请求下载成功")


def step11_transfer_data(canUds, file_data, progress_callback=None):
    """step11: 传输数据 TRANSFILE, chunkSize=4093（transferFile 失败时返回 False 而不抛异常，需检查）"""
    res, err = canUds.transferFile(fileData=file_data, chunkSize=4093,
                                   progress_callback=progress_callback)
    if not res:
        # err: 1=传输中无响应 2=等待响应超时 3=响应序列号不匹配
        raise Exception(f"step11_transferdata0 数据传输失败 (错误码: {err})")
    total_blocks = len(file_data) // 4093 + (1 if len(file_data) % 4093 else 0)
    _log(f"[step11_transferdata0] 数据传输完成 共 {total_blocks} 块")


def step12_transfer_exit(canUds):
    """step12: 传输结束 37 -> 77"""
    uds_send(canUds, IsoServices.RequestTransferExit, [],
             confirm=[], timeout=5.0)
    _log("[step12_RequestTransferExit0] 传输结束")


def step13_crc_check(canUds, crc):
    """step13: CRC校验 31 01 02 12 + crc -> 71 01 02 12 10 00"""
    crc_bytes = list(crc.to_bytes(4, 'big'))
    params = [0x01, 0x02, 0x12] + crc_bytes
    uds_send(canUds, IsoServices.RoutineControl, params,
             confirm=[0x01, 0x02, 0x12, 0x10, 0x00], timeout=5.0)
    _log(f"[step13_CRC] CRC校验通过 crc=0x{crc:08X}")


def step14_write_cust_flag(canUds):
    """step14: 写客户标志 2E FC 01 43 55 41 50 -> 6E FC 01"""
    uds_send(canUds, IsoServices.WriteDataByIdentifier,
             [0xFC, 0x01, 0x43, 0x55, 0x41, 0x50],  # "CUAP" = Customer App
             confirm=[0xFC, 0x01], timeout=3.2)
    _log("[step14_write_cust_flag] 客户标志写入成功")


def step19_check_dependencies(canUds):
    """step19: 依赖检查 31 01 02 05"""
    uds_send(canUds, IsoServices.RoutineControl, [0x01, 0x02, 0x05],
             confirm=[], timeout=3.1)
    _log("[step19_Check_dependencies] 依赖检查通过")


def step20_ecu_reset(canUds):
    """step20: ECU复位到默认会话 10 01"""
    uds_send(canUds, IsoServices.DiagnosticSessionControl, [0x01],
             confirm=[0x7F,0x10,0x78], timeout=8.0)
    _log("[step20_ecuReset] ECU复位已发送")


# ======================== 主流程 ========================

def run_ota(canBus, hex_path, progress_callback=None, log_callback=None):
    """
    OTA 升级主流程（总线由调用方创建并负责 shutdown 释放）。
    任一步骤失败抛出 Exception，由调用方捕获提示。
    :param canBus: CAN 总线实例
    :param hex_path: 固件 hex 文件路径
    :param progress_callback: 进度回调 progress_callback(percent, text)，percent 为 0~100
    :param log_callback: 日志回调 log_callback(message, tag)
    """
    global _log_fn

    def _report(percent, text):
        if progress_callback:
            progress_callback(percent, text)

    def _transfer_progress(idx, total):
        # 数据传输阶段占总进度 30% ~ 90%
        if total > 0:
            _report(min(30 + int(60 * idx / total), 90), f"传输固件数据 {idx}/{total}")

    # 切换模块内所有 _log 输出到 GUI 日志
    _log_fn = log_callback or print
    canTp = None

    try:
        _log(f"[OTA] 开始升级 — File: {hex_path}")
        _report(2, "发送安全帧...")

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
        _report(8, "加载固件文件...")
        start_address, file_data, file_length, file_crc = step_load_file(hex_path)

        # ---- step1: 扩展会话 ----
        _report(12, "切换扩展会话...")
        step1_extended_session(canUds)

        # ---- step2: 编程会话 ----
        _report(16, "切换编程会话...")
        step2_programming_session(canUds)

        # ---- step3: 安全访问 ----
        _report(20, "安全访问...")
        step3_security_access(canUds)

        # ---- step5: 擦除 ----
        _report(25, "擦除 Flash...")
        step5_erase_block(canUds, start_address, file_length)

        # ---- step10: 请求下载 ----
        _report(30, "请求下载...")
        step10_request_download(canUds, start_address, file_length)

        # ---- step11: 传输数据 ----
        _report(30, "传输固件数据...")
        step11_transfer_data(canUds, file_data, progress_callback=_transfer_progress)

        # ---- step12: 传输结束 ----
        _report(92, "结束传输...")
        step12_transfer_exit(canUds)

        # ---- step13: CRC校验 ----
        _report(95, "CRC 校验...")
        step13_crc_check(canUds, file_crc)

        # ---- step14: 写客户标志 ----
        _report(97, "写客户标志...")
        step14_write_cust_flag(canUds)

        # ---- step19: 依赖检查 ----
        _report(99, "依赖检查...")
        step19_check_dependencies(canUds)

        # ---- step20: ECU复位 ----
        _report(100, "ECU 复位...")
        # 按文档：复位请求发出后 ECU 可能直接重启不再应答，无响应不影响升级结果
        try:
            step20_ecu_reset(canUds)
        except Exception:
            _log("[OTA] ECU 复位请求已发送", "INFO")

        _log("[OTA] 升级完成！", "OK")

    finally:
        # 只停 ISO-TP 内部线程；总线 shutdown 由调用方负责
        # （必须先停 ISO-TP 再关总线，否则 relay 线程会对已关闭的 handle 读数据报 "Handle is invalid"）
        if canTp is not None:
            canTp.stop()
        # 还原日志输出，避免后续调用指向已失效的 GUI 回调
        _log_fn = print


