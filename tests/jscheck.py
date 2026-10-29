#!/usr/bin/env python3
"""Extract every inline <script> of an HTML file and run `node --check` on it.

Usage: python3 tests/jscheck.py index.html [digylog-admin.html ...]
"""
import os
import re
import subprocess
import sys
import tempfile

files = sys.argv[1:]
if not files:
    print("usage: jscheck.py <file.html> [...]")
    sys.exit(2)

ok = True
for path in files:
    src = open(path, encoding="utf-8").read()
    blocks = []
    for m in re.finditer(r"<script([^>]*)>(.*?)</script>", src, re.S):
        attrs, body = m.group(1), m.group(2)
        if "src=" in attrs or not body.strip():
            continue
        blocks.append((attrs.strip(), body))
    for i, (attrs, body) in enumerate(blocks, 1):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
            fh.write(body)
            tmp = fh.name
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode != 0:
            ok = False
            print("%s block %d attrs=[%s] -> FAIL" % (path, i, attrs[:60]))
            print(r.stderr[:900])
        else:
            print("%s block %d attrs=[%s] len=%d -> OK" % (path, i, attrs[:60], len(body)))
print("ALL OK" if ok else "SYNTAX ERRORS")
sys.exit(0 if ok else 1)
