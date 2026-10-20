"""Sayt (shop/downloads.py) yasaydigan plagin ZIP'ining namunasini yaratadi - Windows dastur testi uchun.
Ishlatish: python tools/sample_zip.py ziptest/TT.zip"""
import io
import json
import sys
import zipfile

out = sys.argv[1]
manifest = {"prefix": "TT", "name": "Tez-Tez", "version": "", "description": "", "bot": "", "files": ["TezTez.gms"]}
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("plagin/TezTez.gms", b"gms-ichi")
    z.writestr("plagin/manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    z.writestr("O'qing.txt", "namuna")
print("tayyor:", out)
