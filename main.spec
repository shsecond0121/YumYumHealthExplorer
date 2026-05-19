# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('Hakgyoansim_SiganpyoR.ttf', '.'), ('Quicksand.ttf', '.'), ('icon.ico', '.'), ('냠냠건강탐험대icon.png', '.'), ('team_mate', 'team_mate')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # numpy: pygame이 surfarray/sndarray로 옵션 import. 게임 코드는 아예 안 씀 (grep 0건).
        # numpy.libs/libopenblas 단독 36MB라 가장 큰 절감원.
        'numpy', 'numpy.core', 'numpy.linalg', 'numpy.random', 'numpy.fft',
        'pygame.surfarray', 'pygame.sndarray',
        # 네트워킹/암호화 stdlib — 게임에서 안 씀 (urllib/http/email은 pathlib 의존이라 보존)
        'ssl', '_ssl', '_hashlib', '_socket', 'socket',
        # 비동기/멀티프로세싱 — 안 씀
        'asyncio', '_asyncio', '_overlapped',
        'multiprocessing', '_multiprocessing',
        # 압축 — 안 씀 (zlib만 pygame 내부에서 필요)
        'lzma', '_lzma', 'bz2', '_bz2',
        # 기타 stdlib 안 씀
        'decimal', '_decimal', 'sqlite3', '_sqlite3', '_wmi',
        'tkinter', '_tkinter', 'turtle', 'turtledemo', 'idlelib',
        'unittest', 'test', 'pydoc', 'pydoc_data',
        'pdb', 'doctest',
    ],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='냠냠건강탐험대',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    icon='icon.ico',
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
