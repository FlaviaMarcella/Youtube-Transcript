# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file para YouTube Transcriber Pro
Gera um executável standalone com FFmpeg incluído automaticamente
"""
import os
import sys
from pathlib import Path

block_cipher = None

# Dados a serem incluídos no bundle
datas = [
    ('assets', 'assets'),
]

# Incluir FFmpeg local se disponível
ffmpeg_path = Path(os.path.expanduser("~")) / ".youtube_transcriber" / "ffmpeg" / "bin"
if ffmpeg_path.exists():
    datas.append((str(ffmpeg_path), 'ffmpeg/bin'))

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'customtkinter',
        'yt_dlp',
        'whisper',
        'PIL',
        'tkinter',
        'numpy',
        'torch',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YouTubeTranscriberPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI mode - sem console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo.png',  # Usar logo como ícone da aplicação
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='YouTubeTranscriberPro',
)
