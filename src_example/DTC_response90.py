import can
import struct
import time
import random
from typing import List, Tuple

# ============================================================
# DTC 消息发送模拟器 (修复版)
# ============================================================

# CAN ID 定义
CAN_IDS = {
    'FL_GROUP1': 0x400,
    'FL_GROUP2': 0x401,
    'FR_GROUP1': 0x402,
    'FR_GROUP2': 0x403,
    'RL_GROUP1': 0x404,
    'RL_GROUP2': 0x405,
    'RR_GROUP1': 0x406,
    'RR_GROUP2': 0x407,
}

# DTC 条目配置 (GROUP1: entry1~5)
# 每个条目: (status_byte, type_byte, num_start, ts_start)
# 注意: 大端序下，4字节字段从起始字节开始连续存放
GROUP1_ENTRIES = [
    (49, 48, 44, 40),  # entry1: status, type, num(44-47), ts(40-43)
    (39, 38, 34, 30),  # entry2: status, type, num(34-37), ts(30-33)
    (29, 28, 24, 20),  # entry3: status, type, num(24-27), ts(20-23)
    (19, 18, 14, 10),  # entry4: status, type, num(14-17), ts(10-13)
    (9,  8,  4,  0),   # entry5: status, type, num(4-7),   ts(0-3)
]

# DTC 条目配置 (GROUP2: entry6~11)
GROUP2_ENTRIES = [
    (29, 28, 24, 20),  # entry6: status, type, num(24-27), ts(20-23)
    (39, 38, 34, 30),  # entry7: status, type, num(34-37), ts(30-33)
    (49, 48, 44, 40),  # entry8: status, type, num(44-47), ts(40-43)
    (59, 58, 54, 50),  # entry9: status, type, num(54-57), ts(50-53)
    (9,  8,  4,  0),   # entry10: status, type, num(4-7),   ts(0-3)
    (19, 18, 14, 10),  # entry11: status, type, num(14-17), ts(10-13)
]


def build_group1_message(
    timestamp_ms: int,
    frame_number: int,
    dtc_number: int,
    dtc_entries: List[Tuple[int, int, int, int]]  # (dtc_num, dtc_type, status_mask, change_ts)
) -> bytes:
    """
    构建 GROUP1 消息 (64字节)
    """
    data = bytearray(64)  # 初始化为0
    
    # 填充帧头 (大端序)
    struct.pack_into('>I', data, 54, timestamp_ms)      # Byte54-57: 时间戳
    data[53] = dtc_number & 0xFF                         # Byte53: DTC数量
    data[52] = 0x10                                      # Byte52: MessageType (固定0x10)
    struct.pack_into('>H', data, 50, frame_number & 0xFFFF)  # Byte50-51: 帧序号
    
    # 填充 DTC 条目
    for i in range(min(dtc_number, len(GROUP1_ENTRIES))):
        if i < len(dtc_entries):
            status_byte, type_byte, num_start, ts_start = GROUP1_ENTRIES[i]
            dtc_num, dtc_type, status_mask, change_ts = dtc_entries[i]
            
            # 填充 DTC 编码 (4字节，大端序)
            struct.pack_into('>I', data, num_start, dtc_num & 0xFFFFFFFF)
            
            # 填充 DTC 类型 (1字节)
            data[type_byte] = dtc_type & 0xFF
            
            # 填充状态掩码 (1字节)
            data[status_byte] = status_mask & 0xFF
            
            # 填充变化时间戳 (4字节，大端序)
            struct.pack_into('>I', data, ts_start, change_ts & 0xFFFFFFFF)
    
    return bytes(data)


def build_group2_message(
    dtc_entries: List[Tuple[int, int, int, int]]  # (dtc_num, dtc_type, status_mask, change_ts)
) -> bytes:
    """
    构建 GROUP2 消息 (64字节)
    """
    data = bytearray(64)
    
    # 填充 DTC 条目
    for i in range(min(len(dtc_entries), len(GROUP2_ENTRIES))):
        status_byte, type_byte, num_start, ts_start = GROUP2_ENTRIES[i]
        dtc_num, dtc_type, status_mask, change_ts = dtc_entries[i]
        
        # 填充 DTC 编码 (4字节，大端序)
        struct.pack_into('>I', data, num_start, dtc_num & 0xFFFFFFFF)
        
        # 填充 DTC 类型 (1字节)
        data[type_byte] = dtc_type & 0xFF
        
        # 填充状态掩码 (1字节)
        data[status_byte] = status_mask & 0xFF
        
        # 填充变化时间戳 (4字节，大端序)
        struct.pack_into('>I', data, ts_start, change_ts & 0xFFFFFFFF)
    
    return bytes(data)


def generate_sample_dtc_entry(entry_num: int, current_ts: int) -> Tuple[int, int, int, int]:
    """生成示例 DTC 条目"""
    # 示例 DTC 编码
    dtc_codes = {
        1: 0xC1280001,  # 雷达通信故障
        2: 0xC1280002,  # 雷达配置故障
        3: 0xC1280003,  # 雷达温度过高
        4: 0xC1280004,  # 雷达信号丢失
        5: 0xC1280005,  # 雷达内部错误
        6: 0xC1280006,
        7: 0xC1280007,
        8: 0xC1280008,
        9: 0xC1280009,
        10: 0xC1280010,
        11: 0xC1280011,
    }
    
    # dtc_type: bit0=本轮上电故障发生, bit1=本轮上电发生过故障, bit2=上轮上电发生过故障
    if entry_num <= 3:
        dtc_type = 0x01  # 当前故障
    elif entry_num <= 6:
        dtc_type = 0x02  # 本轮发生过
    else:
        dtc_type = 0x00  # 无故障
    
    # status_mask (示例值)
    status_mask = 0x01 if entry_num % 2 == 0 else 0x03
    
    dtc_num = dtc_codes.get(entry_num, 0xC1280999)
    change_ts = max(0, current_ts - entry_num * 500)  # 确保不为负数
    
    return (dtc_num, dtc_type, status_mask, change_ts)


class DTCMessageSimulator:
    """DTC 消息发送模拟器"""
    
    def __init__(self, channel: str = "1", bitrate: int = 500000, data_bitrate: int = 2000000):
        try:
            self.canBus = can.interface.Bus(
                interface="kvaser",
                channel=channel,
                bitrate=bitrate,
                data_bitrate=data_bitrate,
                fd=True,
            )
            print(f"[INFO] CAN 总线初始化成功 - channel: {channel}")
        except Exception as e:
            print(f"[ERROR] CAN 总线初始化失败: {e}")
            raise
        
        self.frame_counter = 0
        self.start_time = int(time.time() * 1000)  # 模拟上电时间
    
    def get_uptime_ms(self) -> int:
        """获取模拟的上电时间（毫秒）"""
        return int(time.time() * 1000) - self.start_time
    
    def send_group1(self, node: str, dtc_entries: List[Tuple[int, int, int, int]]):
        """发送 GROUP1 消息"""
        if node not in ['FL', 'FR', 'RL', 'RR']:
            print(f"[ERROR] 无效节点: {node}")
            return
        
        can_id = CAN_IDS[f'{node}_GROUP1']
        current_ts = self.get_uptime_ms()
        
        data = build_group1_message(
            timestamp_ms=current_ts,
            frame_number=self.frame_counter % 65536,
            dtc_number=len(dtc_entries),
            dtc_entries=dtc_entries
        )
        
        msg = can.Message(
            arbitration_id=can_id,
            data=data,
            is_fd=True,
            is_extended_id=False,
            dlc=64
        )
        
        try:
            self.canBus.send(msg)
            print(f"[TX] {node}_GROUP1 (0x{can_id:03X}): TS={current_ts}ms, "
                  f"DTC_Num={len(dtc_entries)}, Frame={self.frame_counter % 65536}")
            # 打印前几个字节用于调试
            print(f"     Data[0:16]: {data[:16].hex()}")
        except Exception as e:
            print(f"[ERROR] 发送 GROUP1 失败: {e}")
    
    def send_group2(self, node: str, dtc_entries: List[Tuple[int, int, int, int]]):
        """发送 GROUP2 消息"""
        if node not in ['FL', 'FR', 'RL', 'RR']:
            print(f"[ERROR] 无效节点: {node}")
            return
        
        can_id = CAN_IDS[f'{node}_GROUP2']
        
        data = build_group2_message(dtc_entries=dtc_entries)
        
        msg = can.Message(
            arbitration_id=can_id,
            data=data,
            is_fd=True,
            is_extended_id=False,
            dlc=64
        )
        
        try:
            self.canBus.send(msg)
            print(f"[TX] {node}_GROUP2 (0x{can_id:03X}): {len(dtc_entries)} DTC entries")
            # 打印前几个字节用于调试
            print(f"     Data[0:16]: {data[:16].hex()}")
        except Exception as e:
            print(f"[ERROR] 发送 GROUP2 失败: {e}")
    
    def send_full_dtc_report(self, node: str):
        """发送完整的 DTC 报告 (GROUP1 + GROUP2)"""
        current_ts = self.get_uptime_ms()
        
        # 生成 GROUP1 的 5 个 DTC (Entry1~5)
        group1_entries = []
        for i in range(1, 6):
            group1_entries.append(generate_sample_dtc_entry(i, current_ts))
        
        # 生成 GROUP2 的 6 个 DTC (Entry6~11)
        group2_entries = []
        for i in range(6, 12):
            group2_entries.append(generate_sample_dtc_entry(i, current_ts))
        
        # 发送消息
        print(f"\n--- 发送 {node} 节点 DTC 报告 (Frame {self.frame_counter}) ---")
        self.send_group1(node, group1_entries)
        time.sleep(0.005)  # 间隔5ms
        self.send_group2(node, group2_entries)
        
        self.frame_counter += 1
        
        return (group1_entries, group2_entries)
    
    def send_multi_node_report(self, nodes: List[str] = None):
        """发送多个节点的 DTC 报告"""
        if nodes is None:
            nodes = ['FL', 'FR', 'RL', 'RR']
        
        for node in nodes:
            self.send_full_dtc_report(node)
            time.sleep(0.01)  # 间隔10ms
    
    def send_custom_dtc(self, node: str, group: int, entries: List[Tuple[int, int, int, int]]):
        """发送自定义 DTC 数据"""
        if group == 1:
            self.send_group1(node, entries)
        elif group == 2:
            self.send_group2(node, entries)
        else:
            print(f"[ERROR] 无效 GROUP: {group}")
    
    def start_periodic_send(self, node: str, interval_ms: int = 100):
        """周期发送 DTC 消息"""
        print(f"\n=== 开始周期发送 {node} 节点 DTC 消息 (间隔 {interval_ms}ms) ===")
        print("按 Ctrl+C 停止\n")
        
        try:
            while True:
                self.send_full_dtc_report(node)
                time.sleep(interval_ms / 1000.0)
        except KeyboardInterrupt:
            print("\n[INFO] 用户停止发送")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """关闭 CAN 总线"""
        try:
            self.canBus.shutdown()
            print("[INFO] CAN 总线已关闭")
        except:
            pass


# ============================================================
# 使用示例
# ============================================================

def main():
    # 创建模拟器
    try:
        simulator = DTCMessageSimulator(
            channel="1",
            bitrate=500000,
            data_bitrate=2000000
        )
    except Exception as e:
        print(f"[ERROR] 无法创建模拟器: {e}")
        return
    
    try:
        # 方式1: 发送单个节点的完整 DTC 报告
        print("=== 方式1: 发送单个节点 DTC 报告 ===")
        simulator.send_full_dtc_report('FL')
        time.sleep(0.5)
        
        # 方式2: 发送所有节点的 DTC 报告
        print("\n=== 方式2: 发送所有节点 DTC 报告 ===")
        simulator.send_multi_node_report(['FL', 'FR', 'RL', 'RR'])
        time.sleep(0.5)
        
        # 方式3: 发送自定义 DTC 数据
        print("\n=== 方式3: 发送自定义 DTC 数据 ===")
        custom_entries = [
            (0xDEADBEEF, 0x01, 0x01, 1000),
            (0xCAFEBABE, 0x02, 0x03, 2000),
            (0x12345678, 0x01, 0x05, 3000),
        ]
        simulator.send_custom_dtc('FR', 1, custom_entries)
        
        # 方式4: 周期发送 (取消注释以启用)
        # print("\n=== 方式4: 周期发送 ===")
        # simulator.start_periodic_send('FL', interval_ms=100)
        
    except Exception as e:
        print(f"[ERROR] 运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        simulator.shutdown()


if __name__ == "__main__":
    main()