# -*- coding: utf-8 -*-
"""雷达诊断管理 GUI —— OTA 升级 / DTC 读取清除 / 标定和标定查询（具体功能布局部分）"""

import os
import sys
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from PIL import Image, ImageTk

from gui_styles import (ORANGE_PRIMARY, ORANGE_LIGHT, BG_CARD, TEXT_DARK,ORANGE_ACCENT, 
                        CARD_PAD, SECTION_GAP, LOG_COLORS,
                        _FlatButton, _SideButton, setup_styles)


class RadarDiagnosticsGUI:
    """雷达诊断管理主界面：侧栏导航 + CAN 配置 + 功能面板 + 日志区"""

    def __init__(self, root):
        self.root = root
        self.root.title("WF Radar Diagnostics Manager | ©2021 无锡威孚高科技集团股份有限公司 版权所有")
        self.root.geometry("1200x750")
        self.root.configure(bg=BG_CARD)

        # 使用 iconphoto 方法设置窗口图标（跨平台兼容，Linux/Windows/macOS 均支持）
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'images', 'tool.png')
        if os.path.exists(icon_path):
            icon_img = ImageTk.PhotoImage(Image.open(icon_path))
            self.root.iconphoto(True, icon_img)

        setup_styles()              # 初始化样式
        self._build_main_layout()   # 构建主布局
        self._build_sidebar()       # 构建侧栏导航
        self._build_can_config()    # CAN 配置面板
        self._build_ota_panel()     # OTA 面板
        self._build_dtc_panel()     # DTC 面板
        self._build_cal_panel()     # 标定 面板
        self._build_oa_panel()     # OA 面板
        self._build_log_area()      # 构建日志区域
        self._show_ota_panel()      # 显示 OTA 升级面板

    def _build_main_layout(self):
        """构建主布局：顶部导航栏 + 侧栏导航 + 主内容区域 + 日志区域"""

        self.top_frame = tk.Frame(self.root, bg=BG_CARD)
        self.top_frame.pack(fill=tk.BOTH, expand=True, padx=SECTION_GAP, pady=(SECTION_GAP, 0))

        self.sidebar = tk.Frame(self.top_frame, bg=BG_CARD, width=180)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, SECTION_GAP))
        self.sidebar.pack_propagate(False)

        self.main_area = tk.Frame(self.top_frame, bg=BG_CARD)
        self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.bottom_frame = tk.Frame(self.root, bg=BG_CARD, height=330)
        self.bottom_frame.pack(fill=tk.BOTH, expand=False, padx=SECTION_GAP, pady=SECTION_GAP)
        self.bottom_frame.pack_propagate(False)

    def _build_sidebar(self):
        """构建侧栏导航：包含 OTA 升级、 DTC 读取清除、 标定和查询按钮"""
        logo_frame = tk.Frame(self.sidebar, bg=BG_CARD)
        logo_frame.pack(fill=tk.X, pady=(8, 0))

        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../images/logo.png')
        if not os.path.exists(logo_path):
            logo_path = './images/logo.png'
        img = Image.open(logo_path)
        img = img.resize((155, 23), Image.LANCZOS)
        self._logo_img = ImageTk.PhotoImage(img)
        tk.Label(logo_frame, image=self._logo_img, bg=BG_CARD).pack(anchor=tk.W, padx=4)

        header = tk.Frame(self.sidebar, bg=BG_CARD)
        header.pack(fill=tk.X, pady=(4, 12))

        tk.Label(header, text=" 雷达诊断管理 V1.5.1", font=('Microsoft YaHei', 12, 'bold italic'),
                        fg=ORANGE_ACCENT, bg=BG_CARD).pack(anchor=tk.W)

        tk.Frame(self.sidebar, bg=ORANGE_LIGHT, height=1).pack(fill=tk.X, pady=(0, 12))

        self.btn_ota = _SideButton(self.sidebar, text="◈  OTA 升级",command=None, bg=BG_CARD, height=60)
        self.btn_ota.pack(pady=(0, 4), anchor=tk.W)

        self.btn_dtc = _SideButton(self.sidebar, text="◈  DTC 读取/清除",command=None, bg=BG_CARD, height=60)
        self.btn_dtc.pack(pady=(0, 4), anchor=tk.W)

        self.btn_cal = _SideButton(self.sidebar, text="◈  标定和查询",command=None, bg=BG_CARD, height=60)
        self.btn_cal.pack(pady=(0, 4), anchor=tk.W)

        self.btn_oa = _SideButton(self.sidebar, text="◈  OA 结果",command=None, bg=BG_CARD, height=60)
        self.btn_oa.pack(pady=(0, 4), anchor=tk.W)

        tk.Frame(self.sidebar, bg=ORANGE_LIGHT, height=1).pack(fill=tk.X, pady=(12, 12))

        info_frame = tk.Frame(self.sidebar, bg=BG_CARD)
        info_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.conn_status_var = tk.StringVar(value="●  未连接")
        self.conn_status_label = tk.Label(info_frame, textvariable=self.conn_status_var,
                                          font=('Microsoft YaHei', 12),fg=ORANGE_ACCENT, bg=BG_CARD)
        self.conn_status_label.pack(anchor=tk.W, pady=(0, 4))

    def _build_can_config(self):
        """构建 CAN 配置面板：包含通道、波特率、数据波特率"""
        card = ttk.Frame(self.main_area, style='Card.TFrame')
        card.pack(fill=tk.X, pady=(0, SECTION_GAP))

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill=tk.X, padx=CARD_PAD[0], pady=CARD_PAD[1])

        tk.Label(inner, text="CAN 总线配置", font=('Microsoft YaHei', 10, 'bold'),
                 fg=TEXT_DARK, bg=BG_CARD).pack(anchor=tk.W, pady=(0, 2))

        grid = tk.Frame(inner, bg=BG_CARD)
        grid.pack(fill=tk.X)

        # 通道选择
        tk.Label(grid, text="Channel", font=('Microsoft YaHei', 9),
                 fg=ORANGE_ACCENT, bg=BG_CARD).grid(row=0, column=0, sticky=tk.W, pady=4, padx=(0, 8))
        self.channel_var = tk.StringVar()
        self.channel_combo = ttk.Combobox(grid, textvariable=self.channel_var,
                                          width=45, state="readonly")
        self.channel_combo.grid(row=0, column=1, sticky=tk.W, pady=4, padx=(0, 20))

        # 波特率选择
        tk.Label(grid, text="Bitrate", font=('Microsoft YaHei', 9),
                 fg=ORANGE_ACCENT, bg=BG_CARD).grid(row=0, column=2, sticky=tk.W, pady=4, padx=(0, 8))
        self.bitrate_var = tk.StringVar(value="500000")
        self.bitrate_combo = ttk.Combobox(grid, textvariable=self.bitrate_var, width=10,
                                          values=["125000", "250000", "500000", "1000000"])
        self.bitrate_combo.grid(row=0, column=3, sticky=tk.W, pady=4, padx=(0, 20))

        # 数据波特率选择
        tk.Label(grid, text="Data Bitrate", font=('Microsoft YaHei', 9),
                 fg=ORANGE_ACCENT, bg=BG_CARD).grid(row=0, column=4, sticky=tk.W, pady=4, padx=(0, 8))
        self.data_bitrate_var = tk.StringVar(value="2000000")
        self.data_bitrate_combo = ttk.Combobox(grid, textvariable=self.data_bitrate_var, width=10,
                                               values=["500000", "1000000", "2000000", "5000000"])
        self.data_bitrate_combo.grid(row=0, column=5, sticky=tk.W, pady=4, padx=(0, 20))

        # 连接、刷新通道按钮
        btn_row = tk.Frame(inner, bg=BG_CARD)
        btn_row.pack(fill=tk.X, pady=(8, 8))

        self.btn_connect = _FlatButton(btn_row, text="连 接", bg=ORANGE_PRIMARY,
                                       hover=ORANGE_ACCENT, width=90, height=32)
        self.btn_connect.pack(side=tk.LEFT, padx=(0, 20))

        self.btn_refresh = _FlatButton(btn_row, text="刷新通道", bg="#FFD8D8",
                                       fg=ORANGE_PRIMARY, hover=ORANGE_LIGHT,width=90, height=32)
        self.btn_refresh.pack(side=tk.LEFT)

    def _build_ota_panel(self):
        """构建 OTA 升级面板"""
        self.ota_panel = ttk.Frame(self.main_area, style='Card.TFrame')

        # 外层容器
        inner = tk.Frame(self.ota_panel, bg=BG_CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=CARD_PAD[0], pady=CARD_PAD[1])

        # 标题
        tk.Label(inner, text="OTA 升级", font=('Microsoft YaHei', 11, 'bold'),
                 fg=TEXT_DARK, bg=BG_CARD).pack(anchor=tk.W, pady=(0, 10))

        # ---- 固件文件选择 ----
        section_file = ttk.LabelFrame(inner, text="固件文件", style='Card.TLabelframe')
        section_file.pack(fill=tk.X, pady=(0, 8))

        file_inner = tk.Frame(section_file, bg=BG_CARD)
        file_inner.pack(fill=tk.X, padx=CARD_PAD[0], pady=CARD_PAD[1])

        self.ota_file_var = tk.StringVar()
        self.ota_file_entry = ttk.Entry(file_inner, textvariable=self.ota_file_var,
                                        width=45, state="readonly", font=('Microsoft YaHei', 9))
        self.ota_file_entry.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_ota_browse = _FlatButton(file_inner, text="浏览", bg=ORANGE_PRIMARY,
                                          hover=ORANGE_ACCENT, width=60, height=28)
        self.btn_ota_browse.pack(side=tk.LEFT)

        # ---- 操作按钮 ----
        section_action = ttk.LabelFrame(inner, text="操作", style='Card.TLabelframe')
        section_action.pack(fill=tk.X)

        action_inner = tk.Frame(section_action, bg=BG_CARD)
        action_inner.pack(fill=tk.X, padx=CARD_PAD[0], pady=CARD_PAD[1])

        self.btn_ota_start = _FlatButton(action_inner, text="开始升级", bg=ORANGE_PRIMARY,
                                         hover=ORANGE_ACCENT, width=100, height=32)
        self.btn_ota_start.pack(side=tk.LEFT, padx=(0, 10))

        # ---- 版本查询 ----
        section_ver = ttk.LabelFrame(inner, text="版本查询", style='Card.TLabelframe')
        section_ver.pack(fill=tk.X, pady=(8, 0))

        ver_inner = tk.Frame(section_ver, bg=BG_CARD)
        ver_inner.pack(fill=tk.X, padx=CARD_PAD[0], pady=CARD_PAD[1])

        # FL 版本查询
        fl_frame = tk.Frame(ver_inner, bg=BG_CARD)
        fl_frame.pack(fill=tk.X)

        self.btn_ver_fl = _FlatButton(fl_frame, text="查询 FL 版本", bg=ORANGE_PRIMARY,
                                       hover=ORANGE_ACCENT, width=110, height=32)
        self.btn_ver_fl.pack(side=tk.LEFT, padx=(0, 10))

        self.ver_fl_sw_var = tk.StringVar(value="软件版本: --")
        tk.Label(fl_frame, textvariable=self.ver_fl_sw_var,
                 font=('Microsoft YaHei', 9), fg=TEXT_DARK, bg=BG_CARD).pack(side=tk.LEFT, padx=(0, 16))

        self.ver_fl_hw_var = tk.StringVar(value="硬件版本: --")
        tk.Label(fl_frame, textvariable=self.ver_fl_hw_var,
                 font=('Microsoft YaHei', 9), fg=TEXT_DARK, bg=BG_CARD).pack(side=tk.LEFT)

        # FR 版本查询
        fr_frame = tk.Frame(ver_inner, bg=BG_CARD)
        fr_frame.pack(fill=tk.X, pady=(4, 0))

        self.btn_ver_fr = _FlatButton(fr_frame, text="查询 FR 版本", bg=ORANGE_PRIMARY,
                                       hover=ORANGE_ACCENT, width=110, height=32)
        self.btn_ver_fr.pack(side=tk.LEFT, padx=(0, 10))

        self.ver_fr_sw_var = tk.StringVar(value="软件版本: --")
        tk.Label(fr_frame, textvariable=self.ver_fr_sw_var,
                 font=('Microsoft YaHei', 9), fg=TEXT_DARK, bg=BG_CARD).pack(side=tk.LEFT, padx=(0, 16))

        self.ver_fr_hw_var = tk.StringVar(value="硬件版本: --")
        tk.Label(fr_frame, textvariable=self.ver_fr_hw_var,
                 font=('Microsoft YaHei', 9), fg=TEXT_DARK, bg=BG_CARD).pack(side=tk.LEFT)

    def _build_dtc_panel(self):
        """构建 DTC 读取/清除面板"""
        self.dtc_panel = ttk.Frame(self.main_area, style='Card.TFrame')

        inner = tk.Frame(self.dtc_panel, bg=BG_CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=CARD_PAD[0], pady=CARD_PAD[1])

        tk.Label(inner, text="DTC 读取/清除", font=('Microsoft YaHei', 11, 'bold'),
                 fg=TEXT_DARK, bg=BG_CARD).pack(anchor=tk.W, pady=(0, 10))

        btn_frame = tk.Frame(inner, bg=BG_CARD)
        btn_frame.pack(fill=tk.X, pady=(0, 8))

        self.btn_dtc_start = _FlatButton(btn_frame, text="开始接收", bg=ORANGE_PRIMARY,
                                         hover=ORANGE_ACCENT, width=100, height=32)
        self.btn_dtc_start.pack(side=tk.LEFT, padx=(0, 10))

        self.dtc_status_var = tk.StringVar(value="● 未接收")
        tk.Label(btn_frame, textvariable=self.dtc_status_var,
                 font=('Microsoft YaHei', 9), fg=ORANGE_ACCENT, bg=BG_CARD).pack(side=tk.LEFT, padx=(10, 0))

        tree_frame = tk.Frame(inner, bg=BG_CARD)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('node', 'status_mask', 'dtc_type', 'dtc_num', 'fault_label', 'change_ts')
        self.dtc_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)

        col_widths = {'node': 10, 'status_mask': 90, 'dtc_type': 160, 'dtc_num': 120, 'fault_label': 160, 'change_ts': 120}
        col_labels = {'node': '节点', 'status_mask': 'StatusMask', 'dtc_type': 'DTC类型', 'dtc_num': 'DTC码', 'fault_label': '故障描述', 'change_ts': '变化时间戳(ms)'}
        for col in columns:
            self.dtc_tree.heading(col, text=col_labels.get(col, col))   # 设置列标题
            self.dtc_tree.column(col, width=col_widths.get(col, 100), anchor=tk.CENTER)   # 设置列宽度

        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.dtc_tree.yview)
        self.dtc_tree.configure(yscrollcommand=tree_scroll.set)

        self.dtc_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.dtc_tree.tag_configure('even_row', background='white')
        self.dtc_tree.tag_configure('odd_row', background='#FFF0E0')

        self._dtc_refresh_id = None

    def dtc_set_buttons_state(self, running):
        """设置 DTC 操作按钮状态"""
        if running:
            self.btn_dtc_start.set_enabled(False)
            self.dtc_status_var.set("● 接收中")
        else:
            self.btn_dtc_start.set_enabled(True)
            self.dtc_status_var.set("● 未接收")

    def dtc_update_table(self, all_entries):
        """更新 DTC 表格数据，并将 change_ts 不为 0 的条目持久化到日志文件"""
        for item in self.dtc_tree.get_children():
            self.dtc_tree.delete(item)

        if all_entries is None:
            return

        # 收集所有 change_ts 不为 0 的 DTC 条目，用于写入日志文件
        changed_entries = []

        row_idx = 0
        for node in ['FL', 'FR',]:# 'RL', 'RR'注释，暂时不使用后角
            # 遍历每个节点的 DTC 条目
            entries = all_entries.get(node, [])
            for entry in entries:
                # 遍历每个 DTC 条目
                dtc_type_str = ','.join(entry.get('dtc_type_labels', []))# 合并 DTC 类型标签
                status_str = ','.join(entry.get('status_mask_labels', []))# 合并 StatusMask 标签
                tag = 'even_row' if row_idx % 2 == 0 else 'odd_row'# 根据行索引选择偶数行或奇数行标签
                self.dtc_tree.insert('', tk.END, values=(
                    node,
                    f"0x{entry.get('status_mask', 0):02X} ({status_str})",
                    f"0x{entry.get('dtc_type', 0):02X} ({dtc_type_str})",
                    f"0x{entry.get('dtc_num', 0):08X}",
                    entry.get('fault_label', ''),
                    entry.get('change_ts', 0),
                ), tags=(tag,))
                row_idx += 1

                # 仅保存 change_ts 不为 0 的条目（表示 DTC 状态发生过变化）
                if entry.get('change_ts', 0) != 0:
                    entry['_dtc_type_str'] = dtc_type_str
                    entry['_status_str'] = status_str
                    changed_entries.append(entry)

        # 如果有发生变化的 DTC 条目，写入日志文件持久化存储
        if changed_entries:
            # 首次写入时生成文件名并创建文件，同一运行中后续写入追加到同一个文件
            if getattr(self, '_dtc_log_path', None) is None:#_dtc_log_path ：文件名仅在首次生成（None 时生成）
                log_dir = os.path.join(os.getcwd(), 'OUT')
                os.makedirs(log_dir, exist_ok=True)
                filename = datetime.now().strftime('%Y%m%d%H%M%S') + '_DTC.log'
                self._dtc_log_path = os.path.join(log_dir, filename)
            ts = datetime.now().strftime("%H:%M:%S")
            write_mode = 'w' if not getattr(self, '_dtc_log_written', False) else 'a'
            self._dtc_log_written = True
            with open(self._dtc_log_path, write_mode, encoding='utf-8') as f:
                for entry in changed_entries:
                    f.write(
                        f"[{ts}] Node={entry.get('node')} | Group={entry.get('group')} | Entry={entry.get('entry')} | "
                        f"StatusMask=0x{entry.get('status_mask', 0):02X} ({entry.get('_status_str', '')}) | "
                        f"DTC_Type=0x{entry.get('dtc_type', 0):02X} ({entry.get('_dtc_type_str', '')}) | "
                        f"DTC_Num=0x{entry.get('dtc_num', 0):08X} | ChangeTS={entry.get('change_ts', 0)}\n"
                    )

    def _build_cal_panel(self):
        """构建 标定和标定查询面板"""
        self.cal_panel = ttk.Frame(self.main_area, style='Card.TFrame')

        inner = tk.Frame(self.cal_panel, bg=BG_CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=CARD_PAD[0], pady=CARD_PAD[1])

        tk.Label(inner, text="标定和标定查询", font=('Microsoft YaHei', 11, 'bold'),
                 fg=TEXT_DARK, bg=BG_CARD).pack(anchor=tk.W, pady=(0, 10))

        section_static = ttk.LabelFrame(inner, text="静态标定", style='Card.TLabelframe')
        section_static.pack(fill=tk.X, pady=(0, 8))

        static_inner = tk.Frame(section_static, bg=BG_CARD)
        static_inner.pack(fill=tk.X, padx=CARD_PAD[0], pady=CARD_PAD[1])

        self.btn_static_1 = _FlatButton(static_inner, text="左前雷达静态标定", bg=ORANGE_PRIMARY,
                                        hover=ORANGE_ACCENT, width=140, height=32)
        self.btn_static_1.pack(side=tk.LEFT, padx=(0, 8))
        self.btn_static_2 = _FlatButton(static_inner, text="右前雷达静态标定", bg=ORANGE_PRIMARY,
                                        hover=ORANGE_ACCENT, width=140, height=32)
        self.btn_static_2.pack(side=tk.LEFT, padx=(0, 8))
        self.btn_static_3 = _FlatButton(static_inner, text="左后雷达静态标定", bg=ORANGE_PRIMARY,
                                        hover=ORANGE_ACCENT, width=140, height=32)
        self.btn_static_3.pack(side=tk.LEFT, padx=(0, 8))
        self.btn_static_4 = _FlatButton(static_inner, text="右后雷达静态标定", bg=ORANGE_PRIMARY,
                                        hover=ORANGE_ACCENT, width=140, height=32)
        self.btn_static_4.pack(side=tk.LEFT)

        section_param = ttk.LabelFrame(inner, text="标定外参配置", style='Card.TLabelframe')
        section_param.pack(fill=tk.X, pady=(0, 8))

        param_inner = tk.Frame(section_param, bg=BG_CARD)
        param_inner.pack(fill=tk.X, padx=CARD_PAD[0], pady=CARD_PAD[1])

        tk.Label(param_inner, text="参数从 config/config_c.ini 读取",
                 font=('Microsoft YaHei', 9), fg=ORANGE_ACCENT, bg=BG_CARD).pack(anchor=tk.W)

        btn_row = tk.Frame(param_inner, bg=BG_CARD)
        btn_row.pack(anchor=tk.W, pady=(8, 0))

        self.btn_param_1 = _FlatButton(btn_row, text="左前雷达下发参数", bg=ORANGE_PRIMARY,
                                       hover=ORANGE_ACCENT, width=130, height=32)
        self.btn_param_1.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_param_2 = _FlatButton(btn_row, text="右前雷达下发参数", bg=ORANGE_PRIMARY,
                                       hover=ORANGE_ACCENT, width=130, height=32)
        self.btn_param_2.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_param_3 = _FlatButton(btn_row, text="左后雷达下发参数", bg=ORANGE_PRIMARY,
                                       hover=ORANGE_ACCENT, width=130, height=32)
        self.btn_param_3.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_param_4 = _FlatButton(btn_row, text="右后雷达下发参数", bg=ORANGE_PRIMARY,
                                       hover=ORANGE_ACCENT, width=130, height=32)
        self.btn_param_4.pack(side=tk.LEFT, padx=(0, 6))

        btn_row2 = tk.Frame(param_inner, bg=BG_CARD)
        btn_row2.pack(anchor=tk.W, pady=(6, 0))

        self.btn_clear_1 = _FlatButton(btn_row2, text="左前雷达清除参数", bg="#FFF5D8",
                                       fg=ORANGE_PRIMARY, hover=ORANGE_LIGHT, width=130, height=32)
        self.btn_clear_1.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_clear_2 = _FlatButton(btn_row2, text="右前雷达清除参数", bg="#FFF5D8",
                                       fg=ORANGE_PRIMARY, hover=ORANGE_LIGHT, width=130, height=32)
        self.btn_clear_2.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_clear_3 = _FlatButton(btn_row2, text="左后雷达清除参数", bg="#FFF5D8",
                                       fg=ORANGE_PRIMARY, hover=ORANGE_LIGHT, width=130, height=32)
        self.btn_clear_3.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_clear_4 = _FlatButton(btn_row2, text="右后雷达清除参数", bg="#FFF5D8",
                                       fg=ORANGE_PRIMARY, hover=ORANGE_LIGHT, width=130, height=32)
        self.btn_clear_4.pack(side=tk.LEFT)

    def _set_cal_buttons_state(self, state):
        """设置 标定和标定查询 操作按钮状态"""
        for i in range(1, 5):
            for prefix in ('btn_static_', 'btn_param_', 'btn_clear_'):
                getattr(self, prefix + str(i)).configure(state=state)

    def _build_oa_panel(self):
        """构建 OA 结果面板"""
        self.oa_panel = ttk.Frame(self.main_area, style='Card.TFrame')

        inner = tk.Frame(self.oa_panel, bg=BG_CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=CARD_PAD[0], pady=CARD_PAD[1])

        tk.Label(inner, text="OA 结果", font=('Microsoft YaHei', 11, 'bold'),
                 fg=TEXT_DARK, bg=BG_CARD).pack(anchor=tk.W, pady=(0, 10))

        # 第二通道配置（OA 标定专用）
        chan2_frame = tk.Frame(inner, bg=BG_CARD)
        chan2_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Label(chan2_frame, text="第二通道（OA 标定专用）", font=('Microsoft YaHei', 12),
                 fg=ORANGE_ACCENT, bg=BG_CARD).pack(side=tk.LEFT, padx=(0, 8))

        self.oa_chan2_var = tk.StringVar()
        self.oa_chan2_combo = ttk.Combobox(chan2_frame, textvariable=self.oa_chan2_var,
                                            width=45, state="readonly")
        self.oa_chan2_combo.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_oa_connect2 = _FlatButton(chan2_frame, text="连接通道2", bg=ORANGE_PRIMARY,
                                            hover=ORANGE_ACCENT, width=100, height=32)
        self.btn_oa_connect2.pack(side=tk.LEFT, padx=(0, 10))
        self.btn_oa_disconnect2 = _FlatButton(chan2_frame, text="断开通道2", bg="#FFD8D8",
                                               fg=ORANGE_PRIMARY, hover=ORANGE_LIGHT, width=100, height=32)
        self.btn_oa_disconnect2.pack(side=tk.LEFT)
        self.btn_oa_disconnect2.set_enabled(False)

        self.oa_chan2_status_var = tk.StringVar(value="")
        tk.Label(chan2_frame, textvariable=self.oa_chan2_status_var,
                 font=('Microsoft YaHei', 9), fg="#2E7D32", bg=BG_CARD).pack(side=tk.LEFT, padx=(10, 0))

        # 操作按钮
        btn_frame = tk.Frame(inner, bg=BG_CARD)
        btn_frame.pack(fill=tk.X, pady=(0, 8))

        self.btn_oa_start = _FlatButton(btn_frame, text="开始接收", bg=ORANGE_PRIMARY,
                                        hover=ORANGE_ACCENT, width=100, height=32)
        self.btn_oa_start.pack(side=tk.LEFT, padx=(0, 10))

        self.oa_status_var = tk.StringVar(value="● 未接收")
        tk.Label(btn_frame, textvariable=self.oa_status_var,
                 font=('Microsoft YaHei', 9), fg=ORANGE_ACCENT, bg=BG_CARD).pack(side=tk.LEFT, padx=(10, 0))

        # 传出变量表格
        tree_frame = tk.Frame(inner, bg=BG_CARD)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('node', 'RadarStatus', 'FinalCalibState', 'YawMountAngle',
                   'PitchMountAngle', 'EleOffset', 'AziOffset',
                   'MountPosX', 'MountPosZ', 'MountPosY')
        self.oa_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=4)

        col_widths = {'node': 50, 'RadarStatus': 100, 'FinalCalibState': 110,
                      'YawMountAngle': 100, 'PitchMountAngle': 100,
                      'EleOffset': 90, 'AziOffset': 90,
                      'MountPosX': 90, 'MountPosZ': 90, 'MountPosY': 90}
        col_labels = {'node': '节点', 'RadarStatus': 'RadarStatus',
                      'FinalCalibState': 'FinalCalibState',
                      'YawMountAngle': 'YawMountAngle', 'PitchMountAngle': 'PitchMountAngle',
                      'EleOffset': 'EleOffset', 'AziOffset': 'AziOffset',
                      'MountPosX': 'MountPosX', 'MountPosZ': 'MountPosZ', 'MountPosY': 'MountPosY'}
        for col in columns:
            self.oa_tree.heading(col, text=col_labels.get(col, col))
            self.oa_tree.column(col, width=col_widths.get(col, 100), anchor=tk.CENTER)

        self.oa_tree.tag_configure('even_row', background='white')
        self.oa_tree.tag_configure('odd_row', background='#FFF0E0')
        self.oa_tree.pack(fill=tk.BOTH, expand=True)

        # 初始化 4 行空数据
        for i, node in enumerate(['FL', 'FR', 'RL', 'RR']):
            tag = 'even_row' if i % 2 == 0 else 'odd_row'
            self.oa_tree.insert('', tk.END, iid=node, values=(node, '', '', '', '', '', '', '', '', ''), tags=(tag,))

    def oa_update_table(self, node, data):
        """更新 OA 表格中指定节点的数据"""
        row_data = [node]
        for col in ('CALIB_RadarStatus', 'CALIB_FinalCalibState', 'YawMountAngle',
                     'PitchMountAngle', 'EleOffset', 'AziOffset',
                     'MountPosX', 'MountPosZ', 'MountPosY'):
            val = data.get(col, '')
            if isinstance(val, float):
                row_data.append(f'{val:.4f}')
            else:
                row_data.append(str(val) if val != '' else '')
        if self.oa_tree.exists(node):
            self.oa_tree.item(node, values=row_data)

    def oa_set_buttons_state(self, running):
        """设置 OA 结果接收按钮状态"""
        if running:
            self.btn_oa_start.set_enabled(False)
            self.oa_status_var.set("● 接收中")
            # 运行时不允许操作第二通道连接
            self.btn_oa_connect2.set_enabled(False)
            self.btn_oa_disconnect2.set_enabled(False)
        else:
            self.btn_oa_connect2.set_enabled(True)
            self.btn_oa_start.set_enabled(True)
            self.oa_status_var.set("● 未接收")

    def oa_set_chan2_state(self, connected):
        """设置第二通道连接状态"""
        if connected:
            self.btn_oa_disconnect2.set_enabled(True)
            self.oa_chan2_status_var.set("● 已连接")
        else:
            self.btn_oa_disconnect2.set_enabled(False)
            self.oa_chan2_status_var.set(" ")

    def _build_log_area(self):
        """构建日志区域：显示 CAN 通讯日志"""
        card = ttk.Frame(self.bottom_frame, style='Card.TFrame')
        card.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=CARD_PAD[0], pady=CARD_PAD[1])

        header = tk.Frame(inner, bg=BG_CARD)
        header.pack(fill=tk.X, pady=(0, 6))

        tk.Label(header, text="通讯日志", font=('Microsoft YaHei', 10, 'bold'),
                 fg=TEXT_DARK, bg=BG_CARD).pack(side=tk.LEFT)

        # 时间同步勾选框（最右侧）
        self.time_sync_var = tk.BooleanVar()
        self.chk_time_sync = tk.Checkbutton(header, text="时间同步",
                                            variable=self.time_sync_var,
                                            bg=BG_CARD, fg=ORANGE_ACCENT,
                                            selectcolor=BG_CARD,
                                            activebackground=BG_CARD,
                                            font=('Microsoft YaHei', 9))
        self.chk_time_sync.pack(side=tk.RIGHT, padx=(0, 6))

        # 日志颜色图例
        legend = tk.Frame(header, bg=BG_CARD)
        legend.pack(side=tk.RIGHT)

        for label, color in [("SEND", LOG_COLORS["SEND"]), ("RECV", LOG_COLORS["RECV"]),
                             ("ERROR", LOG_COLORS["ERROR"]), ("OK", LOG_COLORS["OK"])]:
            # 构建日志颜色图例
            dot = tk.Frame(legend, bg=color, width=8, height=8)
            dot.pack(side=tk.LEFT, padx=(2, 4))
            tk.Label(legend, text=label, font=('Microsoft YaHei', 10),
                     fg=ORANGE_ACCENT, bg=BG_CARD).pack(side=tk.LEFT)

        text_frame = tk.Frame(inner, bg=BG_CARD)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # 日志文本框
        self.log_text = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED,
                                font=("Consolas", 10), bg='#FAFAFA', fg=TEXT_DARK,
                                bd=1, relief='solid', highlightthickness=0,
                                selectbackground=ORANGE_LIGHT, padx=8, pady=6)
        log_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL,
                                   command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        for tag, color in LOG_COLORS.items():
            # 配置日志标签颜色
            self.log_text.tag_config(tag, foreground=color)

    def _hide_all_panels(self):
        """隐藏所有面板"""
        for panel in [self.ota_panel, self.dtc_panel, self.cal_panel, self.oa_panel]:
            panel.pack_forget()

    def _show_ota_panel(self):
        """显示 OTA 操作面板"""
        self._hide_all_panels()
        self.ota_panel.pack(fill=tk.BOTH, expand=True)
        self.btn_ota.set_active(True)
        self.btn_dtc.set_active(False)
        self.btn_cal.set_active(False)
        self.btn_oa.set_active(False)

    def _show_dtc_panel(self):
        """显示 DTC 操作面板"""
        self._hide_all_panels()
        self.dtc_panel.pack(fill=tk.BOTH, expand=True)
        self.btn_dtc.set_active(True)
        self.btn_ota.set_active(False)
        self.btn_cal.set_active(False)
        self.btn_oa.set_active(False)

    def _show_cal_panel(self):
        """显示 标定和标定查询 操作面板"""
        self._hide_all_panels()
        self.cal_panel.pack(fill=tk.BOTH, expand=True)
        self.btn_cal.set_active(True)
        self.btn_ota.set_active(False)
        self.btn_dtc.set_active(False)
        self.btn_oa.set_active(False)

    def _show_oa_panel(self):
        """显示 OA 结果面板"""
        self._hide_all_panels()
        self.oa_panel.pack(fill=tk.BOTH, expand=True)
        self.btn_oa.set_active(True)
        self.btn_ota.set_active(False)
        self.btn_dtc.set_active(False)
        self.btn_cal.set_active(False)

    # ---- 外部接口 ----

    def set_channel_list(self, channels):
        """设置 CAN 通道列表"""
        self.channel_combo["values"] = channels
        self.oa_chan2_combo["values"] = channels
        if channels and not self.channel_var.get():
            self.channel_var.set(channels[0])

    def set_connection_status(self, connected):
        """设置连接状态显示"""
        if connected:
            self.conn_status_var.set("●  已连接")
            self.conn_status_label.configure(fg="#2E7D32")
        else:
            self.conn_status_var.set("●  未连接")
            self.conn_status_label.configure(fg=ORANGE_ACCENT)

    def get_channel_info(self):
        """获取当前选择的 CAN 通道、波特率和数据波特率"""
        return self.channel_var.get(), self.bitrate_var.get(), self.data_bitrate_var.get()

    def get_channel_number(self):
        """获取当前选择的 CAN 通道编号"""
        channel_str = self.channel_var.get()
        return channel_str.split(":")[0].strip() if channel_str else ""

    def oa_get_channel2_number(self):
        """获取 OA 第二通道编号"""
        channel_str = self.oa_chan2_var.get()
        return channel_str.split(":")[0].strip() if channel_str else ""

    def log(self, message, tag="INFO"):
        """
        将日志消息添加到文本框中（线程安全）
        标定操作通过 threading.Thread 跑在子线程里。
        当子线程调用 gui.log() 时，log_text.insert 操作实际是在子线程中执行的。
        
        Tkinter 的设计规则是：
        所有控件操作必须在创建这些控件的线程（即主线程/GUI线程）中执行。 
        从其他线程操作控件，内部数据结构会产生竞态条件，轻则丢数据，重则 SIGSEGV（段错误）。
        """
        ts = datetime.now().strftime("%H:%M:%S")
        def _write():
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{ts}]-- {message}\n", tag)
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.root.after_idle(_write)

    def download_log(self):
        """自动保存日志到 OUT/ 目录，文件名为年月日时分秒.log"""
        out_dir = os.path.join(os.getcwd(), 'OUT')
        os.makedirs(out_dir, exist_ok=True)
        filename = datetime.now().strftime('%Y%m%d%H%M%S') + '.log'
        filepath = os.path.join(out_dir, filename)
        content = self.log_text.get('1.0', tk.END)
        if content.strip():# 检查是否有内容，不为空时才保存
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
