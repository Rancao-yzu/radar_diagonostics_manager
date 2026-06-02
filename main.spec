# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=[
        'lib',       # 让 PyInstaller 能找到 lib/ 下的 isotp、uds、can_config
    ],
    binaries=[],
    datas=[
        ('lib/uds/uds_communications/Uds/config.ini', 'lib/uds/uds_communications/Uds/'),  # UDS 内部 config
    ],
    hiddenimports=[
        'can.interfaces.kvaser',          # python-can 的 Kvaser 后端
        'can.interfaces.socketcan',       # python-can 的 SocketCAN 后端
        'isotp',                          # ISO-TP 协议栈
        'uds',
        'uds.uds_communications',
        'uds.uds_communications.Uds',
        'uds.uds_config_tool',
        'uds.uds_configuration',
        'uds.uds_tools',
        'PIL._tkinter_finder',            # PIL 与 tkinter 的桥接
        'configparser',                   # 保证 ini 解析能正常导入
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'unittest',
        'test',
        'pydoc',
        'distutils',
        'setuptools',
        'pip',
        'pkg_resources',
        'http',
        'xmlrpc',
        'wsgiref',
        'curses',
        'ensurepip',
        'lib2to3',

        # ---- 新增排除：已确认可安全排除的无关模块 ----
        'multiprocessing',                # 多进程，只用了 threading
        'xml',                            # XML 解析（只用 configparser 读 ini）
        'html',                           # HTML 解析
        'gettext',                        # 国际化翻译
        'netrc',                          # .netrc 认证
        'ftplib',                         # FTP
        'smtplib',                        # SMTP
        'poplib',                         # POP3
        'imaplib',                        # IMAP4
        'nntplib',                        # NNTP
        'telnetlib',                      # Telnet
        'webbrowser',                     # 浏览器控制
        'turtle',                         # Turtle 绘图
        'venv',                           # 虚拟环境
        'zipapp',                         # zipapp
        'doctest',                        # 文档测试
        'statistics',                     # 统计函数

        # ---- pip 第三方库排除：安装了但项目完全不用的库 ----
        'numpy',                          # 数值计算 ~50MB
        'pandas',                         # 数据分析 ~30MB
        'matplotlib',                     # 绑图 ~20MB
        'contourpy',                      # matplotlib 依赖
        'cycler',                         # matplotlib 依赖
        'fonttools',                      # matplotlib 依赖
        'kiwisolver',                     # matplotlib 依赖
        'pyparsing',                      # matplotlib 依赖
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='images\\tool.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
