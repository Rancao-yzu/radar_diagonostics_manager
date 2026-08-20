# -*- coding: utf-8 -*-
"""版本与更新说明弹窗 —— 解析 config/config_updata.ini 并以排版后的样式展示"""

import os
import tkinter as tk
from tkinter import ttk

from .gui_styles import ORANGE_PRIMARY, ORANGE_ACCENT, BG_CARD, TEXT_DARK


def _parse_versions(config_path):
    """解析 config_updata.ini，返回 [{version, date, items}, ...]"""
    versions = []
    current = None
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.rstrip('\n')
                stripped = line.strip()
                # 形如 [V1.5.3] 的 section 头
                if stripped.startswith('[') and stripped.endswith(']'):
                    if current:
                        versions.append(current)
                    current = {'version': stripped[1:-1], 'date': '', 'items': []}
                elif current is not None and stripped.startswith(';'):
                    # 去掉行首分号及空白
                    content = stripped[1:].strip()
                    if not content:
                        continue
                    if content.startswith('更新日期:'):
                        current['date'] = content[len('更新日期:'):].strip()
                    elif content.startswith('- '):
                        current['items'].append(content[2:].strip())
                    elif content.startswith('-'):
                        current['items'].append(content[1:].strip())
                    else:
                        current['items'].append(content)
            if current:
                versions.append(current)
    except Exception as e:
        versions = [{'version': '错误', 'date': '', 'items': [f'无法读取版本说明文件: {e}']}]
    return versions


def show_version_dialog(parent, config_path=None):
    """弹出模态窗口展示版本与更新说明"""
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'config', 'config_updata.ini')

    versions = _parse_versions(config_path)

    win = tk.Toplevel(parent)
    win.title("版本与更新说明")
    win.geometry("720x600")
    win.configure(bg=BG_CARD)
    win.transient(parent)
    win.wait_visibility()   # 等待窗口被映射后再 grab，避免 X11 下 "grab failed: window not viewable"
    win.grab_set()

    # ---- 内容区 ----
    text = tk.Text(win, wrap=tk.WORD, font=('Microsoft YaHei', 10),
                  fg=TEXT_DARK, bg=BG_CARD, padx=20, pady=14,
                  relief='flat', highlightthickness=0, cursor='arrow')
    sb = ttk.Scrollbar(win, orient='vertical', command=text.yview)
    text.configure(yscrollcommand=sb.set)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    text.pack(fill=tk.BOTH, expand=True)

    # ---- 文本标签样式 ----
    text.tag_configure('version', font=('Microsoft YaHei', 13, 'bold'),
                       foreground=ORANGE_ACCENT, spacing1=10, spacing3=2)
    text.tag_configure('date', font=('Microsoft YaHei', 9, 'italic'),
                       foreground='#888888')
    text.tag_configure('separator', foreground='#CCCCCC',
                       spacing1=2, spacing3=6)
    text.tag_configure('item', lmargin1=22, lmargin2=22,
                       font=('Microsoft YaHei', 10),
                       foreground=TEXT_DARK, spacing1=2, spacing3=2)

    # ---- 渲染各版本 ----
    for i, ver in enumerate(versions):
        if i > 0:
            text.insert('end', '\n')
        text.insert('end', ver['version'], 'version')
        if ver['date']:
            text.insert('end', '    ' + ver['date'], 'date')
        text.insert('end', '\n')
        text.insert('end', '─' * 10 + '\n', 'separator')
        for item in ver['items']:
            text.insert('end', '•  ' + item + '\n', 'item')

    text.configure(state='disabled')
    win.update_idletasks()
    # 居中显示在父窗口
    if parent is not None and parent.winfo_exists():
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w = win.winfo_width()
        h = win.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        win.geometry(f'+{max(0, x)}+{max(0, y)}')
