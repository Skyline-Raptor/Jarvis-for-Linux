"""Check bundled file hashes before installation. A receipt, not a digital signature."""
import hashlib
import json
import sys
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1]
    manifest=json.loads((root/'release-manifest.json').read_text(encoding='utf-8'))
    errors=[]
    for relative,record in manifest['files'].items():
        path=root/relative
        if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file():
            errors.append(relative+': missing or unsafe path');continue
        digest=hashlib.sha256()
        with path.open('rb') as source:
            for block in iter(lambda:source.read(1024*1024),b''):digest.update(block)
        if path.stat().st_size!=record['bytes'] or digest.hexdigest()!=record['sha256']:
            errors.append(relative+': changed')
    if errors:
        print('\n'.join(errors));return 1
    print('Verified',len(manifest['files']),'bundled files. This checks consistency, not publisher authenticity.')
    return 0


if __name__=='__main__':raise SystemExit(main())
