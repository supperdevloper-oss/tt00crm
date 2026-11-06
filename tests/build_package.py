#!/usr/bin/env python3
"""Build the deployable package of the CRM.

The package contains only the files that have to be uploaded to the web root
of https://paraveda.store/ :

    api.php  index.html  digylog-admin.html  .htaccess

The zip is reproducible (fixed timestamps, deflate 9) so the SHA256 of the
package identifies exactly what was shipped.

Usage: python3 tests/build_package.py [name]
"""
import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = sys.argv[1] if len(sys.argv) > 1 else "paraveda-mobile-v4.zip"
FILES = ["api.php", "index.html", "digylog-admin.html", ".htaccess"]
FIXED = (2026, 11, 6, 12, 0, 0)

out = ROOT / NAME
if out.exists():
    out.unlink()
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for name in FILES:
        info = zipfile.ZipInfo(name, date_time=FIXED)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, (ROOT / name).read_bytes())

data = out.read_bytes()
print("%s  %d bytes" % (NAME, len(data)))
print("sha256 " + hashlib.sha256(data).hexdigest())
with zipfile.ZipFile(out) as z:
    print("entries: " + ", ".join(z.namelist()))
    assert z.testzip() is None
    for name in z.namelist():
        assert z.read(name) == (ROOT / name).read_bytes(), name
print("package OK")
