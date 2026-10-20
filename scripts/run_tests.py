import datetime
import io
import json
import os
import sys
import time
import unittest
from pathlib import Path

def main():
    root=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root))
    os.chdir(root)
    out=root/'test-results'
    out.mkdir(exist_ok=True)
    started=time.monotonic()
    stream=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(root/'tests'))
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    report=stream.getvalue()
    print(report)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    (out/(stamp+'.txt')).write_text(report,encoding='utf-8')
    summary=dict(at=stamp,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),seconds=round(time.monotonic()-started,3),python=sys.version,platform=sys.platform,native_windows=sys.platform=='win32')
    (out/'latest.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':
    raise SystemExit(main())
