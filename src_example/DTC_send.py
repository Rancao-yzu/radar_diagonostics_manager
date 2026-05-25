import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))

import can
import isotp
from uds import UdsMessage, IsoServices, Uds  # UDS 协议库：消息构造、服务ID定义、核心操作类
import time 
# 导入 UDS 标准的枚举定义，用于 DTC 相关服务的子功能号和状态掩码
from uds.uds_config_tool.ISOStandard.ISOStandard import (
    IsoReadDTCSubfunction,  # 读取 DTC 的子功能枚举（如按状态掩码读取、读取数量等）
    IsoReadDTCStatusMask,   # DTC 状态掩码枚举（如 testFailed、confirmedDTC 等）
    IsoDiagnosticSessionType,  # 诊断会话类型枚举（默认会话、扩展会话、编程会话等）
)

def hybrid_delay_second(seconds):
    end_ns = time.perf_counter_ns() + int(seconds * 1e9)
    remaining = end_ns - time.perf_counter_ns()
    # 如果剩余时间大于 5ms，先用 sleep 让出 CPU（提前 1ms 醒来）
    if remaining > 5_000_000:
        time.sleep((remaining - 1_000_000) / 1e9)
    # 最后 1ms 以内用忙等确保精确延时
    while time.perf_counter_ns() < end_ns:
        pass


# ============================================================
# 工具函数：将 3 字节的 DTC 原始数据解析为可读格式
# 例如 [0x12, 0x34, 0x56] -> "P123456"
# DTC 编码规则(ISO 15031-6):
#   第一个字节的高 2 位表示组别: 00=P(动力总成), 01=C(底盘), 10=B(车身), 11=U(网络)
#   剩余位组合成 P+4 位数字的标准格式
# ============================================================
def format_dtc(dtc_bytes):
    if len(dtc_bytes) < 3:
        return hex(dtc_bytes[0]) if dtc_bytes else "N/A"

    # DTC 组别映射：0=Powertrain, 1=Chassis, 2=Body, 3=Network
    group_map = {0: "P", 1: "C", 2: "B", 3: "U"}
    # 取第一个字节的高 2 位确定组别
    group = group_map.get((dtc_bytes[0] >> 6) & 0x03, "?")
    # 第一个字节的低 6 位
    first = dtc_bytes[0] & 0x3F
    second = dtc_bytes[1]
    third = dtc_bytes[2]

    return f"{group}{first:02X}{second:02X}{third:02X}"


# ============================================================
# 工具函数：根据子功能号格式化 DTC 响应数据并打印
# 不同的子功能返回的数据结构不同，需要分别处理
# ============================================================
def format_dtc_response(subfunction, data):
    # 打印分隔线
    print(f"\n{'='*60}")
    print(f"  ReadDTCInformation - subfunction 0x{subfunction:02X}")

    if len(data) < 1:
        print("  [Empty response]")
        return

    # 情况1：读取 DTC 数量（子功能 0x01）
    # 响应格式: [statusAvailability, dtcFormatIdentifier, dtcCountHigh, dtcCountLow]
    if subfunction in (IsoReadDTCSubfunction.reportNumberOfDTCByStatusMask,):
        idx = 0
        status_avail = data[idx]  # 状态可用性字节
        idx += 1
        dtc_format = data[idx]  # DTC 格式标识符
        idx += 1
        dtc_count = (data[idx] << 8) | data[idx + 1]  # DTC 数量（大端 2 字节）
        idx += 2
        print(f"  DTCStatusAvailability:  0x{status_avail:02X}")
        print(f"  DTCFormatIdentifier:    0x{dtc_format:02X}")
        print(f"  DTC Count:              {dtc_count}")

    # 情况2：按状态掩码读取 DTC 详细信息（子功能 0x02）
    # 响应格式: [statusAvailability, dtcFormat, countH, countL, dtc1_3bytes, status1, dtc2_3bytes, status2, ...]
    elif subfunction in (IsoReadDTCSubfunction.reportDTCByStatusMask,):
        idx = 0
        status_avail = data[idx]
        idx += 1
        dtc_format = data[idx]
        idx += 1
        dtc_count = (data[idx] << 8) | data[idx + 1]  # 本次返回的 DTC 数量
        idx += 2
        print(f"  DTCStatusAvailability:  0x{status_avail:02X}")
        print(f"  DTCFormatIdentifier:    0x{dtc_format:02X}")
        print(f"  DTC Count:              {dtc_count}")

        if dtc_count == 0:
            print("  No DTC stored.")
            return

        # 遍历每个 DTC，每个占 4 字节：3 字节 DTC 代码 + 1 字节状态
        for i in range(dtc_count):
            if idx + 4 > len(data):
                break
            dtc_code = data[idx:idx+3]  # 3 字节 DTC 代码
            dtc_status = data[idx + 3]  # 1 字节 DTC 状态
            idx += 4
            print(f"    DTC #{i+1}: {format_dtc(dtc_code):10s}  "
                  f"Status: 0x{dtc_status:02X} "
                  f"({' | '.join(_decode_dtc_status(dtc_status))})")

    # 情况3：读取支持的 DTC（子功能 0x0A），按原始字节输出
    elif subfunction in (IsoReadDTCSubfunction.reportSupportedDTC,):
        for i, b in enumerate(data):
            print(f"    byte[{i:3d}] = 0x{b:02X}")

    # 其他子功能：按原始字节输出
    else:
        for i, b in enumerate(data):
            print(f"    byte[{i:3d}] = 0x{b:02X}")

    print(f"{'='*60}\n")


# ============================================================
# 工具函数：将 DTC 状态字节按位拆解为可读的标签列表
# DTC 状态字节的每一位代表不同的状态含义（ISO 14229-1）
# ============================================================
def _decode_dtc_status(status):
    bits = []
    if status & 0x01:
        bits.append("testFailed")  # bit0: 当前测试失败
    if status & 0x02:
        bits.append("testFailedThisCycle")  # bit1: 本次监测周期测试失败
    if status & 0x04:
        bits.append("pendingDTC")  # bit2: 待定 DTC
    if status & 0x08:
        bits.append("confirmedDTC")  # bit3: 已确认 DTC
    if status & 0x10:
        bits.append("testNotCompletedSinceLastClear")  # bit4: 上次清除后未完成测试
    if status & 0x20:
        bits.append("testFailedSinceLastClear")  # bit5: 上次清除后测试失败
    if status & 0x40:
        bits.append("testNotCompletedThisCycle")  # bit6: 本次监测周期未完成测试
    if status & 0x80:
        bits.append("warningIndicator")  # bit7: 警告指示灯请求
    return bits if bits else ["none"]


# ============================================================
# 封装函数：发送 UDS 请求并等待 ECU 响应
# 参数:
#   canUds   - Uds 实例
#   service  - UDS 服务 ID（如 0x19=ReadDTCInformation, 0x14=ClearDiagnosticInformation）
#   params   - 服务参数列表
#   timeout  - 等待响应超时时间（秒）
#   confirm  - 期望的响应确认字节，用于校验响应是否正确
#   PrintLog - 是否打印日志
# 返回:
#   (是否成功, UdsMessage响应对象)
# ============================================================
def send_uds(canUds, service, params, timeout=2.0,
             confirm=None, PrintLog=True):
    # 构造 UDS 请求消息：服务ID + 参数
    msg = UdsMessage()
    msg.create(service, params)
    # 发送并等待响应
    res, resp = canUds.send(msg, timeout=timeout, confirm=confirm or [],
                            PrintLog=PrintLog)
    return res, resp


# ============================================================
# 读取 DTC 详细信息（按状态掩码过滤）
# 参数:
#   status_mask - DTC 状态掩码（0xFF = 所有状态，0x08 = 仅已确认的 DTC 等）
#   subfunction- 子功能（默认 0x02 = reportDTCByStatusMask）
# ============================================================
def read_dtc_by_status(canUds, status_mask=0xFF,
                       subfunction=None):
    if subfunction is None:
        subfunction = IsoReadDTCSubfunction.reportDTCByStatusMask

    # 发送 UDS 0x19 服务（ReadDTCInformation），子功能为按状态掩码读取
    res, resp = send_uds(canUds, IsoServices.ReadDTCInformation,
                         [subfunction, status_mask])
    if res and resp:
        # 解析响应的数据部分（前 2 字节是服务ID和子功能，跳过）
        format_dtc_response(subfunction, resp.frame[2:])
    else:
        print(f"[FAIL] ReadDTCInformation subfn=0x{subfunction:02X}")
    return res, resp


# ============================================================
# 读取 DTC 数量（子功能 0x01）
# 返回 ECU 中当前存储的 DTC 总数
# ============================================================
def read_dtc_count(canUds, status_mask=0xFF):
    # 发送 UDS 0x19 服务，子功能为 reportNumberOfDTCByStatusMask
    res, resp = send_uds(canUds, IsoServices.ReadDTCInformation, [
        IsoReadDTCSubfunction.reportNumberOfDTCByStatusMask, status_mask])
    if res and resp:
        format_dtc_response(IsoReadDTCSubfunction.reportNumberOfDTCByStatusMask,
                           resp.frame[2:])
        # 从响应中提取 DTC 数量（第 4-5 字节，大端序）
        data = resp.frame[2:]
        if len(data) >= 4:
            return (data[2] << 8) | data[3]
    return 0


# ============================================================
# 清除 DTC（UDS 服务 0x14 - ClearDiagnosticInformation）
# group: DTC 组别掩码（0xFFFFFF = 清除所有组别）
#   - 0xFFFFFF: 清除所有 DTC
#   - 0x000000: 清除动力总成(P)组
#   - 特定 3 字节: 清除指定 DTC
# ECU 成功响应会返回 0x54（0x14 + 0x40）
# ============================================================
def clear_dtc(canUds, group=0xFFFFFF):
    # 将 group 转换为 3 字节列表（大端序）
    group_bytes = [(group >> 16) & 0xFF, (group >> 8) & 0xFF, group & 0xFF]
    # 发送清除 DTC 请求，用 confirm=[0x54] 校验响应
    res, resp = send_uds(canUds, IsoServices.ClearDiagnosticInformation,
                         group_bytes, confirm=[0x54], PrintLog=True)
    if res:
        print(f"[OK] ClearDiagnosticInformation (group=0x{group:06X})")
    else:
        print(f"[FAIL] ClearDiagnosticInformation: {resp}")
    return res, resp


# ============================================================
# ISO-TP 传输层参数配置
# 这些参数控制 CAN 总线上的 ISO-TP 通信行为
# ============================================================
isotpArgs = {
    "stmin": 0,                          # 最小间隔时间（0 = 无间隔，ECU 连续发送）
    "override_receiver_stmin": 0.0001,    # 覆盖接收方 stmin（100µs）
    "blocksize": 8,                       # 流控块大小（每次收到几个连续帧后需要流控确认）
    "wftmax": 0,                          # 最大等待帧次数（0 = 禁用等待帧）
    "tx_data_length": 8,                  # CAN 报文数据长度（字节）
    "tx_data_min_length": 8,              # CAN 报文最小数据长度
    "tx_padding": 0,                      # 发送填充字节（用 0x00 填充短报文）
    "rx_flowcontrol_timeout": 5000,       # 等待流控帧超时（毫秒）
    "rx_consecutive_frame_timeout": 5000, # 等待连续帧超时（毫秒）
    "max_frame_size": 8192,               # 单条 ISOTP 消息最大长度（字节）
    "can_fd": True,                       # 启用 CAN FD（灵活数据速率）
    "bitrate_switch": True,               # 启用 BRS（比特率切换，数据段用高速率）
    "rate_limit_enable": False,           # 是否启用速率限制
    "rate_limit_max_bitrate": 1000000,    # 速率限制最大比特率
    "rate_limit_window_size": 0.2,        # 速率限制时间窗口（秒）
    "listen_mode": False,                 # 监听模式（只收不发）
    "blocking_send": True,                # 阻塞发送模式（发送完成才返回）
    "wait_func": hybrid_delay_second,     # 自定义延时函数（用于精确控制发送间隔）
}


if __name__ == "__main__":
    # 初始化 CAN 总线接口（Kvaser CAN FD）
    canBus = can.interface.Bus(
        interface="kvaser",    # Kvaser CAN 接口
        channel="0",           # 通道号
        bitrate=500000,        # 仲裁段比特率 500 kbps（标准 CAN 速率）
        data_bitrate=2000000,  # 数据段比特率 2 Mbps（CAN FD 高速率）
        fd=True,               # 启用 CAN FD
    )

    try:
        # 初始化 ISO-TP 协议栈
        # address 配置：
        #   - Normal_11bits: 标准 11 位 CAN ID 寻址模式
        #   - txid=0x74c: 发送 CAN ID（诊断仪请求 ID）
        #   - rxid=0x7cc: 接收 CAN ID（ECU 响应 ID）
        canTp = isotp.CanStack(
            bus=canBus,
            address=isotp.Address(
                isotp.AddressingMode.Normal_11bits,
                txid=0x74c,
                rxid=0x7cc,
            ),
            params=isotpArgs,
        )

        # 启动 ISO-TP 协议栈（开启接收线程）
        canTp.start()
        # 创建 UDS 通信实例，绑定 ISO-TP 传输层
        canUds = Uds(canTp)

        # ============================================================
        # Step 1: 进入扩展诊断会话 (0x10 0x03)
        # 读取 DTC 和清除 DTC 通常需要在非默认会话下进行
        # UDS 会话控制: 0x10 = DiagnosticSessionControl
        #   0x01 = DefaultSession（默认会话，功能受限）
        #   0x03 = ExtendedDiagnosticSession（扩展诊断会话，支持读写 DTC 等功能）
        # ============================================================
        print("\n[Step 1] Entering ExtendedDiagnosticSession ...")
        res, resp = send_uds(canUds, IsoServices.DiagnosticSessionControl,
                             [IsoDiagnosticSessionType.ExtendedDiagnosticSession],
                             confirm=[0x03])  # 期望响应 [0x50, 0x03]
        if res:
            print("[OK] DiagnosticSessionControl -> ExtendedDiagnosticSession")
        else:
            # 如果扩展会话失败，尝试进入默认会话
            print(f"[WARN] Failed to enter ExtendedSession, trying DefaultSession ...")
            res, resp = send_uds(canUds, IsoServices.DiagnosticSessionControl,
                                 [IsoDiagnosticSessionType.DefaultSession],
                                 confirm=[0x01])  # 期望响应 [0x50, 0x01]
            if not res:
                print("[FAIL] Cannot enter any diagnostic session, abort.")
                canTp.stop()
                exit(1)

        time.sleep(0.1)

        # ============================================================
        # Step 2: 读取 DTC 数量（0x19 0x01）
        # UDS 服务 0x19 = ReadDTCInformation
        # 子功能 0x01 = reportNumberOfDTCByStatusMask
        # 参数 0xFF = 状态掩码（所有状态都统计）
        # ============================================================
        print("\n[Step 2] Read DTC count (all statuses) ...")
        count = read_dtc_count(canUds, status_mask=0xFF)
        print(f"  -> Current DTC count: {count}")

        # ============================================================
        # Step 3: 读取 DTC 详细信息（0x19 0x02）
        # 子功能 0x02 = reportDTCByStatusMask
        # 会列出每个 DTC 的代码和状态信息
        # ============================================================
        print("\n[Step 3] Read DTC details (reportDTCByStatusMask, mask=0xFF) ...")
        read_dtc_by_status(canUds, status_mask=0xFF)

        # ============================================================
        # Step 4: 按特定状态过滤读取 DTC
        # - 仅读取已确认的 DTC (status_mask = 0x08 = confirmedDtc)
        # - 仅读取测试失败的 DTC (status_mask = 0x01 = testFailed)
        # 这样可以只关注特定状态的故障码
        # ============================================================
        print("\n[Step 4] Read confirmed DTCs only ...")
        read_dtc_by_status(canUds,
                           status_mask=IsoReadDTCStatusMask.confirmedDtc)

        print("\n[Step 4b] Read test-failed DTCs ...")
        read_dtc_by_status(canUds,
                           status_mask=IsoReadDTCStatusMask.testFailed)

        # ============================================================
        # Step 5: 清除 DTC（0x14 - ClearDiagnosticInformation）
        # group=0xFFFFFF 表示清除所有组别的 DTC
        # 也可以指定特定 DTC 或特定组别
        # ECU 成功响应: 0x54（正响应 SID）
        # ============================================================
        print("\n[Step 5] Clearing all DTCs (group=0xFFFFFF) ...")
        clear_dtc(canUds, group=0xFFFFFF)

        time.sleep(0.2)

        # ============================================================
        # Step 6: 验证清除结果
        # 再次读取 DTC 数量，确认清除是否成功
        # 如果 count == 0，说明所有 DTC 已成功清除
        # ============================================================
        print("\n[Step 6] Verify - re-read DTC count after clear ...")
        new_count = read_dtc_count(canUds, status_mask=0xFF)
        print(f"  -> DTC count after clear: {new_count}")

        if new_count == 0:
            print("\n  All DTCs successfully cleared!")
        else:
            print(f"\n  {new_count} DTC(s) remaining, re-reading details ...")
            read_dtc_by_status(canUds, status_mask=0xFF)

        # 停止 ISO-TP 协议栈
        canTp.stop()
        print("\n[Done] DTC test completed.")

    finally:
        # 关闭 CAN 总线接口（确保资源释放）
        canBus.shutdown()
