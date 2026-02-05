# -*- mode: python ; coding: utf-8 -*-

import sys

block_cipher = None

a = Analysis(
    ['proxy_gui.py', 'multi_client_proxy.py', 'telegram_bridge.py'],
    pathex=['.', '..'],
    binaries=[],
    datas=[
        ('multi_client_proxy.py', '.'),
        ('../ai_handler.py', '.'),
        ('telegram_bridge.py', '.'),
    ],
    hiddenimports=[
        'meshtastic',
        'meshtastic.mesh_pb2',
        'meshtastic.portnums_pb2',
        'multi_client_proxy',
        'ai_handler',
        'telegram_bridge',
        'telegram',
        'telegram.ext',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'asyncio',
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MeshtasticProxy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MeshtasticProxy',
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='MeshtasticProxy.app',
        icon=None,
        bundle_identifier='com.meshtastic.proxy',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
        },
    )
