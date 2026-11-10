#!/usr/bin/env python3
"""Package only public website assets for Pages; never publish scripts or secrets."""
import shutil
from pathlib import Path
from generate import ROOT, validate_site

validate_site()
out = ROOT / '_site'
if out.exists():
    shutil.rmtree(out)
out.mkdir()
for item in ['index.html','config.json','assets','data']:
    source = ROOT / item
    if source.is_dir():
        shutil.copytree(source,out/item)
    else:
        shutil.copy2(source,out/item)
(out / '.nojekyll').touch()
print('Public site packaged in _site/')
