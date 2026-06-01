# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=[
        'lib',       # 让 PyInstaller 能找到 lib/ 下的 isotp、uds、can_config
    ],
    binaries=[],
    datas=[
        ('config/', 'config/'),           # config_c.ini / config_d.ini
        ('images/', 'images/'),           # logo.png
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
        'tkinter.test',                   # tkinter 测试模块
        'unittest',                       # 单元测试框架
        'test',                           # 通用测试模块
        'pydoc',                          # 文档生成
        'distutils',                      # 打包工具
        'setuptools',                     # 安装工具
        'pip',                            # 包管理器
        'pkg_resources',                  # 资源管理
        'email',                          # 邮件模块
        'http',                           # HTTP 模块
        'xmlrpc',                         # XML-RPC
        'wsgiref',                        # WSGI
        'curses',                         # 终端 UI
        'ensurepip',                      # pip 引导
        'lib2to3',                        # 2to3 转换工具
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
