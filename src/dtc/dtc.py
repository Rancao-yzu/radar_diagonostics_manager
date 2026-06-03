# -*- coding: utf-8 -*-
"""DTC 诊断消息管理模块 —— 配置加载、CAN 消息接收与解析"""

import os
import threading
import configparser
import can

# config_d.ini 配置文件路径（项目根目录下的 config/ 文件夹）
_DTC_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'config', 'config_d.ini'
)

# 四个雷达节点缩写
_RADAR_NODES = ['FL', 'FR', 'RL', 'RR']

class DTCManager:
    """DTC 诊断消息管理器 —— 接收并解析 6 个雷达节点的 DTC CAN 消息

    每个雷达节点有两组消息：
    - GROUP1: 带帧头（时间戳、DTC数量、帧序号）+ 5 个 DTC 条目
    - GROUP2: 纯 6 个 DTC 条目

    每个 DTC 条目 10 字节：
    status_mask(1) + dtc_type(1) + dtc_num(4) + change_ts(4)
    """

    def __init__(self, bus, log_callback=None):
        self.bus = bus                     # 共用 CAN 总线实例
        self.log_callback = log_callback   # 日志回调，输出到 GUI 日志区
        self._running = False              # 接收线程运行标志
        self._thread = None                # 接收线程对象
        self._lock = threading.Lock()      # 数据读写锁，保证线程安全

        # 加载配置文件
        self._config = load_dtc_config()
        self._can_ids = self._config['can_ids']
        self._group1_header = self._config['group1_header']
        self._group1_entries = self._config['group1_entries']
        self._group2_entries = self._config['group2_entries']
        self._dtc_type_bits = self._config['dtc_type']
        self._status_mask_bits = self._config['status_mask']

        # 所有雷达节点的 DTC 数据，结构:
        # { 'FL': [{entry1}, {entry2}, ...], 'FR': [...], ... }
        # 每个 entry 包含: node, group, entry, status_mask, dtc_type, dtc_num, change_ts
        self._all_entries = {}
        self._init_empty_data()

    def _init_empty_data(self):
        """初始化所有雷达节点的空 DTC 数据结构"""
        for node in _RADAR_NODES:
            self._all_entries[node] = []
            for group in ['group1', 'group2']:
                entries_cfg = self._group1_entries if group == 'group1' else self._group2_entries
                for entry_key, (st_byte, tp_byte, num_s, num_e, ts_s, ts_e) in entries_cfg.items():
                    self._all_entries[node].append({
                        'node': node,
                        'group': group,
                        'entry': entry_key,
                        'status_mask': 0,
                        'dtc_type': 0,
                        'dtc_num': 0,
                        'change_ts': 0,
                    })

    def _log(self, msg, tag='INFO'):
        """通过回调输出日志到 GUI"""
        print(msg)
        if self.log_callback:
            self.log_callback(msg, tag)

    def start(self):
        """启动 DTC 消息接收线程"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._thread.start()
        self._log('[DTC] 开始接收 DTC 消息', 'OK')

    def stop(self):
        """停止 DTC 消息接收线程"""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._log('[DTC] 停止接收 DTC 消息', 'INFO')

    def is_running(self):
        """返回接收线程是否正在运行"""
        return self._running

    def _receive_loop(self):
        """接收线程主循环：持续从 CAN 总线读取 DTC 消息并解析

        通过 bus.recv(timeout=0.5) 实现每 0.5 秒检查一次 _running 标志，
        保证停止时能及时退出循环。
        """
        while self._running:
            try:
                msg = self.bus.recv(timeout=0.5)
            except Exception as e:
                print(f'[DTC ERROR] 接收消息异常: {e}')
                continue

            if msg is None:
                continue

            can_id = msg.arbitration_id
            node = self._resolve_node(can_id)
            if node is None:
                continue

            data = msg.data

            # 判断是 GROUP1 还是 GROUP2 消息
            is_group1 = can_id in (
                self._can_ids['fl_group1'], self._can_ids['fr_group1'],
                self._can_ids['rl_group1'], self._can_ids['rr_group1'],
            )

            try:
                if is_group1:
                    self._parse_group1(data, node)
                else:
                    self._parse_group2(data, node)
            except Exception as e:
                print(f'[DTC ERROR] 解析{node}消息失败: {e}')

    def _resolve_node(self, can_id):
        """根据 CAN ID 反查雷达节点缩写（FL/FR/RL/RR），匹配不到返回 None"""
        for node in _RADAR_NODES:
            key_lower = node.lower()
            if can_id == self._can_ids.get(f'{key_lower}_group1') or can_id == self._can_ids.get(f'{key_lower}_group2'):
                return node
        return None

    def _parse_group1(self, data, node):
        """解析 GROUP1 消息（带帧头 + 5 个 DTC 条目）

        先校验 Byte52 的 MessageType 是否为固定值 0x10，
        不匹配则丢弃该帧。
        """
        hdr = self._group1_header
        byte_info = ' '.join(f'{i:02d}:0x{b:02X}' for i, b in enumerate(data))
        print(f'[DTC] {node}| 原始数据: {byte_info}')   #打印原始数据，

        # 校验 MessageType 字段
        message_type = data[hdr['message_type_byte']]
        if message_type != hdr['message_type_fixed_value']:
            return

        # 解析帧头字段
        ts_bytes = hdr['timestamp_bytes']
        timestamp = int.from_bytes(data[ts_bytes[0]:ts_bytes[1]+1], 'big')  # 雷达上电时间戳 (ms)
        dtc_number = data[hdr['number_byte']]                                # DTC 数量
        fn_bytes = hdr['frame_number_bytes']
        frame_number = int.from_bytes(data[fn_bytes[0]:fn_bytes[1]+1], 'big')  # 消息唯一序号

        print(f'[DTC] {node}| 时间戳={timestamp} | DTC数量={dtc_number} | MessageType=0x{message_type:02X} | 帧序号={frame_number}')

        with self._lock:
            # 遍历 GROUP1 的 5 个 DTC 条目，按配置的字节位置逐个解析
            for entry_idx, (entry_key, (st_byte, tp_byte, num_s, num_e, ts_s, ts_e)) in enumerate(self._group1_entries.items()):
                flat_idx = entry_idx
                entry = self._all_entries[node][flat_idx]
                entry['status_mask'] = data[st_byte]
                entry['dtc_type'] = data[tp_byte]
                entry['dtc_num'] = int.from_bytes(data[num_s:num_e+1], 'big')
                entry['change_ts'] = int.from_bytes(data[ts_s:ts_e+1], 'big')

    def _parse_group2(self, data, node):
        """解析 GROUP2 消息（纯 6 个 DTC 条目，无帧头）

        GROUP2 的条目排在 GROUP1 的 5 个条目之后，索引从 5 开始
        """
        g1_count = len(self._group1_entries)
        with self._lock:
            for i, (entry_key, (st_byte, tp_byte, num_s, num_e, ts_s, ts_e)) in enumerate(self._group2_entries.items()):
                flat_idx = g1_count + i  # GROUP2 条目索引 = GROUP1 数量 + 当前序号
                entry = self._all_entries[node][flat_idx]
                entry['status_mask'] = data[st_byte]
                entry['dtc_type'] = data[tp_byte]
                entry['dtc_num'] = int.from_bytes(data[num_s:num_e+1], 'big')
                entry['change_ts'] = int.from_bytes(data[ts_s:ts_e+1], 'big')

    def get_all_data(self):
        """线程安全地获取所有雷达节点的 DTC 数据深拷贝

        Returns:
            dict: { 'FL': [entry, ...], 'FR': [...], 'RL': [...], 'RR': [...] }
            每个 entry 额外包含 dtc_type_labels 和 status_mask_labels 字段
        """
        import copy
        with self._lock:
            data = copy.deepcopy(self._all_entries)
        # 在锁外解析类型标签，避免长时间持锁
        for node in data:
            for entry in data[node]:
                entry['dtc_type_labels'] = self.resolve_dtc_type(entry.get('dtc_type', 0))
                entry['status_mask_labels'] = self.resolve_status_mask(entry.get('status_mask', 0))
        return data

    def resolve_dtc_type(self, dtc_type_byte):
        """解析 dtc_type 字节，返回各 bit 的含义列表（从 config 读取）"""
        results = []
        for bit_pos in range(8):
            if dtc_type_byte & (1 << bit_pos):
                label = self._dtc_type_bits.get(bit_pos, f'bit{bit_pos}')
                results.append(label)
        return results if results else ['无']

    def resolve_status_mask(self, status_byte):
        """解析 status_mask 字节，返回各 bit 的含义列表（从 config 读取）"""
        results = []
        for bit_pos in range(8):
            if status_byte & (1 << bit_pos):
                label = self._status_mask_bits.get(bit_pos, f'bit{bit_pos}')
                results.append(label)
        return results if results else ['无']


def load_dtc_config():
    """从 config/config_d.ini 加载 DTC 配置

    Returns:
        dict: 包含以下键:
            - can_ids:       各雷达节点的 GROUP1/GROUP2 CAN ID
            - group1_header: GROUP1 帧头字段字节位置
            - group1_entries: GROUP1 的 5 个 DTC 条目字节位置
            - group2_entries: GROUP2 的 6 个 DTC 条目字节位置
            - dtc_type:       DTC 类型位定义
            - status_mask:    状态掩码位定义
    """
    cfg = configparser.ConfigParser()
    cfg.read(_DTC_CONFIG_PATH, encoding='utf-8')

    # 解析 CAN ID 配置节
    can_ids = {}
    for key in cfg['can_ids']:
        can_ids[key] = int(cfg.get('can_ids', key), 0)

    # 解析 GROUP1 帧头配置节
    hdr = cfg['group1_header']
    group1_header = {
        'timestamp_bytes': tuple(int(x) for x in hdr.get('timestamp_bytes', '54,57').split(',')),# 时间戳
        'number_byte': int(hdr.get('number_byte', '53')),# DTC 数量字节
        'message_type_byte': int(hdr.get('message_type_byte', '52')),# 固定值应该 = 0x10, 标识DTC诊断消息
        'frame_number_bytes': tuple(int(x) for x in hdr.get('frame_number_bytes', '50,51').split(',')),# 消息唯一序号
        'message_type_fixed_value': int(hdr.get('message_type_fixed_value', '0x10'), 0),# 固定值0x10, 标识DTC诊断消息
    }

    def _parse_entries(section):
        """解析 DTC 条目配置节，返回 {entry_key: (st_byte, tp_byte, num_s, num_e, ts_s, ts_e)}"""
        entries = {}
        for key in cfg[section]:
            vals = [int(x.strip()) for x in cfg.get(section, key).split(',')]
            entries[key] = (vals[0], vals[1], vals[2], vals[3], vals[4], vals[5])
        return entries

    group1_entries = _parse_entries('group1_entries')
    group2_entries = _parse_entries('group2_entries')

    # 解析 DTC 类型位定义
    dtc_type = {int(k.replace('bit', '')): cfg.get('dtc_type', k) for k in cfg['dtc_type']}

    # 解析状态掩码位定义
    status_mask = {int(k.replace('bit', '')): cfg.get('status_mask', k) for k in cfg['status_mask']}

    return {
        'can_ids': can_ids,
        'group1_header': group1_header,
        'group1_entries': group1_entries,
        'group2_entries': group2_entries,
        'dtc_type': dtc_type,
        'status_mask': status_mask,
    }
