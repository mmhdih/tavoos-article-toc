#!/usr/bin/env python3
"""Build a reproducible WordPress ZIP from runtime files only."""
from pathlib import Path
import re
import zipfile

root = Path(__file__).resolve().parents[1]
header = (root / 'tavoos-article-toc.php').read_text()
version = re.search(r'^ \* Version: ([0-9.]+)$', header, re.M).group(1)
stable = re.search(r'^Stable tag: (.+)$', (root / 'readme.txt').read_text(), re.M).group(1)
if version != stable:
    raise SystemExit('Plugin version and Stable tag disagree')
files = [root / n for n in ('tavoos-article-toc.php', 'uninstall.php', 'LICENSE.txt', 'readme.txt')]
for folder in ('assets', 'includes', 'languages'):
    files.extend(p for p in (root / folder).rglob('*') if p.is_file())
target = root / 'dist' / f'tavoos-article-toc-{version}.zip'
target.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(files):
        info = zipfile.ZipInfo('tavoos-article-toc/' + path.relative_to(root).as_posix(), (2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, path.read_bytes())
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    assert 'tavoos-article-toc/tavoos-article-toc.php' in archive.namelist()
print(target)
