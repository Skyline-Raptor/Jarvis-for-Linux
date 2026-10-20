import json
import multiprocessing
import sys
from .config import Config


def main():
    multiprocessing.freeze_support()
    if '--diagnose' in sys.argv:
        from .models import Ollama
        from .diagnostics import report
        c=Config()
        print(json.dumps(report(c,Ollama(c)),indent=2))
        return 0
    if '--self-test' in sys.argv:
        import unittest
        suite=unittest.defaultTestLoader.discover('tests')
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    from .gui import launch
    return launch()


if __name__=='__main__':
    raise SystemExit(main())
