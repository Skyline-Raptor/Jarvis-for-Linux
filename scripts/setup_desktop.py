"""Create a per-user menu entry. The install directory must remain in place."""
import os
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from jarvis.linux_desktop import desktop_entry

def main():
    target=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'applications/jarvis-fresh.desktop'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(desktop_entry(root/'start_jarvis.sh'),encoding='utf-8')
    target.chmod(0o600)
    print('Menu entry:',target)

if __name__=='__main__':
    main()
