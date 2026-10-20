"""Linux desktop boundary. X11 only for observation/control; unknown lock state fails closed."""
import os
import re
import subprocess
from pathlib import Path


def session_type():
    if os.environ.get('XDG_SESSION_TYPE','').lower()=='wayland' or os.environ.get('WAYLAND_DISPLAY'):
        return 'wayland'
    return 'x11' if os.environ.get('DISPLAY') else 'headless'


def require_x11():
    if session_type()!='x11':
        raise RuntimeError('Screen awareness and desktop control require an X11 session. Choose Cinnamon (X11) at login. Chat/files/voice can run under Wayland.')


def ensure_unlocked():
    services=[('org.cinnamon.ScreenSaver','/org/cinnamon/ScreenSaver'),
              ('org.gnome.ScreenSaver','/org/gnome/ScreenSaver'),
              ('org.xfce.ScreenSaver','/org/xfce/ScreenSaver'),
              ('org.freedesktop.ScreenSaver','/org/freedesktop/ScreenSaver')]
    checked=False
    for name,path in services:
        try:
            p=subprocess.run(['gdbus','call','--session','--dest',name,'--object-path',path,
                              '--method',name+'.GetActive'],capture_output=True,text=True,timeout=2)
        except (OSError,subprocess.SubprocessError):
            continue
        if p.returncode==0:
            raw=p.stdout.strip()
            if re.fullmatch(r'\(true,?\)',raw):
                raise PermissionError('Desktop is locked or screensaver is active')
            if re.fullmatch(r'\(false,?\)',raw):
                checked=True
    if not checked:
        raise PermissionError('Cannot verify the Linux screen-lock state; observation/control paused. Check Cinnamon screensaver and your desktop D-Bus session.')


def foreground(config):
    require_x11()
    ensure_unlocked()
    from Xlib import X,display
    d=display.Display()
    try:
        root=d.screen().root
        prop=root.get_full_property(d.intern_atom('_NET_ACTIVE_WINDOW'),X.AnyPropertyType)
        if prop is None or not len(prop.value) or not int(prop.value[0]):
            raise PermissionError('No foreground application window')
        ident=int(prop.value[0])
        window=d.create_resource_object('window',ident)
        if window.get_attributes().map_state!=X.IsViewable:
            raise PermissionError('Foreground window is not visible')
        title_prop=window.get_full_property(d.intern_atom('_NET_WM_NAME'),X.AnyPropertyType)
        title=title_prop.value if title_prop is not None else window.get_wm_name()
        if isinstance(title,bytes):
            title=title.decode('utf-8',errors='replace')
        title=str(title or '')
        wm_class=' '.join(window.get_wm_class() or ())
        if not title or any(x.casefold() in (title+' '+wm_class).casefold() for x in config.get('excluded_windows')) or 'jarvis fresh' in title.casefold():
            raise PermissionError('Foreground window excluded from observation')
        geometry=window.get_geometry()
        position=root.translate_coords(window,0,0)
        left,top=max(0,position.x),max(0,position.y)
        right=min(d.screen().width_in_pixels,position.x+geometry.width)
        bottom=min(d.screen().height_in_pixels,position.y+geometry.height)
        if right<=left or bottom<=top:
            raise PermissionError('Window is outside the visible screen')
        return dict(title=title,window_id=ident,left=left,top=top,width=right-left,height=bottom-top)
    finally:
        d.close()


def desktop_quote(value):
    if any(ord(c)<32 or ord(c)==127 for c in str(value)):
        raise ValueError('Desktop entry paths cannot contain control characters')
    value=str(value).replace('%','%%')
    for char in ('\\','"','`','$'):
        value=value.replace(char,'\\'+char)
    # Desktop files decode string escapes before parsing Exec quoting.
    value=value.replace('\\','\\\\')
    return '"'+value+'"'


def desktop_entry(launcher,tray=False):
    command='/bin/bash '+desktop_quote(Path(launcher).resolve())+(' --tray' if tray else '')
    return '[Desktop Entry]\nType=Application\nName=Jarvis Fresh\nComment=Local personal AI assistant\nExec='+command+'\nIcon=applications-science\nTerminal=false\nCategories=Utility;\nStartupNotify=true\nX-GNOME-Autostart-enabled=true\n'


def startup_path():
    return Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'autostart'/'jarvis-fresh.desktop'


def set_startup(launcher,enabled):
    path=startup_path()
    if enabled:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(desktop_entry(launcher,tray=True),encoding='utf-8')
        path.chmod(0o600)
    else:
        path.unlink(missing_ok=True)
    return path
