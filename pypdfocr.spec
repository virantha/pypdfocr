# -*- mode: python -*-
a = Analysis(['pypdfocr/pypdfocr.py'],
             pathex=['/Users/virantha/dev/ocr'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'pypdfocr'),
          debug=False,
          strip=None,
          upx=True,
          console=True )
