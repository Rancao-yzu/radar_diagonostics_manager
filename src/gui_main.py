# -*- coding: utf-8 -*-
"""雷达诊断管理 GUI —— OTA 升级 / DTC 读取清除 / 标定和标定查询（具体功能布局部分）"""

import os
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk

from gui_styles import (ORANGE_PRIMARY, ORANGE_LIGHT, BG_CARD, TEXT_DARK,ORANGE_ACCENT, 
                        CARD_PAD, SECTION_GAP, LOG_COLORS,
                        _FlatButton, _SideButton, setup_styles)


class RadarDiagnosticsGUI:
    """雷达诊断管理主界面：侧栏导航 + CAN 配置 + 功能面板 + 日志区"""

    def __init__(self, root):
        self.root = root
        self.root.title("WF Radar Diagnostics Manager | ©2021 无锡威孚高科技集团股份有限公司 版权所有")
        self.root.geometry("1100x750")
        self.root.configure(bg=BG_CARD)

        setup_styles()              # 初始化样式
        self._build_main_layout()   # 构建主布局
        self._build_sidebar()       # 构建侧栏导航
        self._build_can_config()    # CAN 配置面板
        self._build_ota_panel()     # OTA 面板
        self._build_dtc_panel()     # DTC 面板
        self._build_cal_panel()     # 标定 面板
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

        tk.Label(header, text="   雷达诊断管理", font=('Microsoft YaHei', 12, 'bold'),
                 fg=ORANGE_PRIMARY, bg=BG_CARD).pack(anchor=tk.W)

        tk.Frame(self.sidebar, bg=ORANGE_LIGHT, height=1).pack(fill=tk.X, pady=(0, 12))

        self.btn_ota = _SideButton(self.sidebar, text="◈  OTA 升级",command=None, bg=BG_CARD, height=60)
        self.btn_ota.pack(pady=(0, 4), anchor=tk.W)

        self.btn_dtc = _SideButton(self.sidebar, text="◈  DTC 读取/清除",command=None, bg=BG_CARD, height=60)
        self.btn_dtc.pack(pady=(0, 4), anchor=tk.W)

        self.btn_cal = _SideButton(self.sidebar, text="◈  标定和查询",command=None, bg=BG_CARD, height=60)
        self.btn_cal.pack(pady=(0, 4), anchor=tk.W)

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
                                          width=30, state="readonly")
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

        inner = tk.Frame(self.ota_panel, bg=BG_CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=CARD_PAD[0], pady=CARD_PAD[1])

        tk.Label(inner, text="OTA 升级", font=('Microsoft YaHei', 11, 'bold'),
                 fg=TEXT_DARK, bg=BG_CARD).pack(anchor=tk.W, pady=(0, 10))

        placeholder = tk.Frame(inner, bg=ORANGE_LIGHT)
        placeholder.pack(fill=tk.BOTH, expand=True)

        ph_inner = tk.Frame(placeholder, bg=ORANGE_LIGHT)
        ph_inner.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(ph_inner, text="OTA 升级功能开发中...",
                 font=('Microsoft YaHei', 14), fg=ORANGE_ACCENT, bg=ORANGE_LIGHT).pack()

    def _build_dtc_panel(self):
        """构建 DTC 读取/清除面板"""
        self.dtc_panel = ttk.Frame(self.main_area, style='Card.TFrame')

        inner = tk.Frame(self.dtc_panel, bg=BG_CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=CARD_PAD[0], pady=CARD_PAD[1])

        tk.Label(inner, text="DTC 读取/清除", font=('Microsoft YaHei', 11, 'bold'),
                 fg=TEXT_DARK, bg=BG_CARD).pack(anchor=tk.W, pady=(0, 10))

        placeholder = tk.Frame(inner, bg=ORANGE_LIGHT)
        placeholder.pack(fill=tk.BOTH, expand=True)

        ph_inner = tk.Frame(placeholder, bg=ORANGE_LIGHT)
        ph_inner.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(ph_inner, text="DTC 读取/清除功能开发中...",
                 font=('Microsoft YaHei', 14), fg=ORANGE_ACCENT, bg=ORANGE_LIGHT).pack()

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

        self.btn_static_left = _FlatButton(static_inner, text="左雷达静态标定", bg=ORANGE_PRIMARY,
                                           hover=ORANGE_ACCENT, width=140, height=32)
        self.btn_static_left.pack(side=tk.LEFT, padx=(0, 12))

        self.btn_static_right = _FlatButton(static_inner, text="右雷达静态标定", bg=ORANGE_PRIMARY,
                                            hover=ORANGE_ACCENT, width=140, height=32)
        self.btn_static_right.pack(side=tk.LEFT)

        section_param = ttk.LabelFrame(inner, text="标定外参配置", style='Card.TLabelframe')
        section_param.pack(fill=tk.X, pady=(0, 8))

        param_inner = tk.Frame(section_param, bg=BG_CARD)
        param_inner.pack(fill=tk.X, padx=CARD_PAD[0], pady=CARD_PAD[1])

        tk.Label(param_inner, text="参数从 config/config_c.ini 读取",
                 font=('Microsoft YaHei', 9), fg=ORANGE_ACCENT, bg=BG_CARD).pack(anchor=tk.W)

        btn_row = tk.Frame(param_inner, bg=BG_CARD)
        btn_row.pack(anchor=tk.W, pady=(8, 0))

        self.btn_param_left = _FlatButton(btn_row, text="左雷达下发参数", bg=ORANGE_PRIMARY,
                                          hover=ORANGE_ACCENT, width=130, height=32)
        self.btn_param_left.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_param_right = _FlatButton(btn_row, text="右雷达下发参数", bg=ORANGE_PRIMARY,
                                           hover=ORANGE_ACCENT, width=130, height=32)
        self.btn_param_right.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_clear_left = _FlatButton(btn_row, text="左雷达清除参数", bg="#FFF5D8",
                                          fg=ORANGE_PRIMARY, hover=ORANGE_LIGHT, width=130, height=32)
        self.btn_clear_left.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_clear_right = _FlatButton(btn_row, text="右雷达清除参数", bg="#FFF5D8",
                                           fg=ORANGE_PRIMARY, hover=ORANGE_LIGHT, width=130, height=32)
        self.btn_clear_right.pack(side=tk.LEFT)

    def _set_cal_buttons_state(self, state):
        """设置标定按钮状态"""
        for btn in (self.btn_static_left, self.btn_static_right,
                     self.btn_param_left, self.btn_param_right,
                     self.btn_clear_left, self.btn_clear_right):
            btn.configure(state=state)

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

        self.btn_download_log = _FlatButton(header, text="↓", bg=ORANGE_PRIMARY,
                                            hover=ORANGE_ACCENT, width=24, height=20)
        self.btn_download_log.pack(side=tk.LEFT, padx=(6, 0))

        legend = tk.Frame(header, bg=BG_CARD)
        legend.pack(side=tk.RIGHT)

        for label, color in [("SEND", LOG_COLORS["SEND"]), ("RECV", LOG_COLORS["RECV"]),
                             ("ERROR", LOG_COLORS["ERROR"]), ("OK", LOG_COLORS["OK"])]:
            dot = tk.Frame(legend, bg=color, width=8, height=8)
            dot.pack(side=tk.LEFT, padx=(2, 4))
            tk.Label(legend, text=label, font=('Microsoft YaHei', 10),
                     fg=ORANGE_ACCENT, bg=BG_CARD).pack(side=tk.LEFT)

        text_frame = tk.Frame(inner, bg=BG_CARD)
        text_frame.pack(fill=tk.BOTH, expand=True)

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
            self.log_text.tag_config(tag, foreground=color)

    def _hide_all_panels(self):
        for panel in [self.ota_panel, self.dtc_panel, self.cal_panel]:
            panel.pack_forget()

    def _show_ota_panel(self):
        self._hide_all_panels()
        self.ota_panel.pack(fill=tk.BOTH, expand=True)
        self.btn_ota.set_active(True)
        self.btn_dtc.set_active(False)
        self.btn_cal.set_active(False)

    def _show_dtc_panel(self):
        self._hide_all_panels()
        self.dtc_panel.pack(fill=tk.BOTH, expand=True)
        self.btn_dtc.set_active(True)
        self.btn_ota.set_active(False)
        self.btn_cal.set_active(False)

    def _show_cal_panel(self):
        self._hide_all_panels()
        self.cal_panel.pack(fill=tk.BOTH, expand=True)
        self.btn_cal.set_active(True)
        self.btn_ota.set_active(False)
        self.btn_dtc.set_active(False)

    # ---- 外部接口 ----

    def set_channel_list(self, channels):
        self.channel_combo["values"] = channels
        if channels and not self.channel_var.get():
            self.channel_var.set(channels[0])

    def set_connection_status(self, connected):
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
        channel_str = self.channel_var.get()
        return channel_str.split(":")[0].strip() if channel_str else ""

    def log(self, message, tag="INFO"):
        """将日志消息添加到文本框中"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def download_log(self):
        """导出日志到文件"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not filepath:
            return
        content = self.log_text.get("1.0", tk.END)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        self.log(f"[INFO] 日志已保存至: {filepath}", "OK")
