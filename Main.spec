# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['Main.py'],
             pathex=['C:\\Users\\LAI8PK\\Desktop\\Projects\\yolo_cylinder\\onnx_code\\code'],
             binaries=[],
             datas=[],
             hiddenimports=['onnxruntime','onnxruntime.capi.onnxruntime_inference_collection','__future__','typing'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts, 
          [],
          exclude_binaries=True,
          name='Vision',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          icon = 'C:\\Users\\LAI8PK\\Desktop\\Projects\\yolo_cylinder\\onnx_code\\code\\static\\icon\\cam_logo.ico',
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          version='version.txt' )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='CYLINDER')