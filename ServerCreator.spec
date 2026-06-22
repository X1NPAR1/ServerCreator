# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification for ServerCreator (one-folder / onedir build).

A one-folder build keeps ``python311.dll`` and every dependency next to the
executable, so there is no per-launch extraction to a temporary directory.
This avoids the "python311.dll not found" failure that can occur with one-file
builds when the application is replaced by the auto-updater while running.

    pyinstaller ServerCreator.spec --noconfirm
    -> dist/ServerCreator/ServerCreator.exe  (+ supporting files)
"""

block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/logo.ico', 'assets')],
    hiddenimports=[],
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
    name='ServerCreator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ServerCreator',
)
