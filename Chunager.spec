# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['.\\Source\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('.\\Source\\extra', './extra/'), ('.\\Source\\img', './img/'), ('.\\Source\\pages', './pages/')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Chunager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
	icon=['.\\Source\\icon.ico'],
	version='.\\Source\\version.rc',
)
