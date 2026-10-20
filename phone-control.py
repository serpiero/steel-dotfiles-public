#!/usr/bin/env python3
"""On-demand scrcpy OTG; no terminal, polling daemon or phone display changes."""
from pathlib import Path
import argparse
import fcntl
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time

UNIT = 'steel-phone-otg.service'
ROOT = Path(__file__).resolve().parent


def capture_library():
    source = ROOT / 'features/phone-control/capture-on-focus.c'
    library = Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid()))) / 'steel-phone-capture.so'
    if not library.exists() or library.stat().st_mtime_ns < source.stat().st_mtime_ns:
        flags = run('pkg-config', '--cflags', '--libs', 'sdl3')
        if flags.returncode:
            raise RuntimeError('SDL3 development support is required for phone control.')
        fd, staging = tempfile.mkstemp(prefix='steel-phone-', suffix='.so', dir=library.parent)
        os.close(fd)
        try:
            result = run('cc', '-shared', '-fPIC', '-O2', str(source), '-o', staging, *flags.stdout.split(), '-ldl')
            if result.returncode: raise RuntimeError(result.stderr.strip())
            os.replace(staging, library)
        finally:
            Path(staging).unlink(missing_ok=True)
    return library


def run(*args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, timeout=8, **kwargs)


def active():
    return run('systemctl', '--user', 'is-active', '--quiet', UNIT).returncode == 0


def manual_sessions():
    """Legacy OTG sessions only: never stop screen mirroring or VNC."""
    sessions = []
    for folder in Path('/proc').glob('[0-9]*'):
        try:
            if folder.stat().st_uid != os.getuid():
                continue
            if (folder / 'exe').resolve().name != 'scrcpy':
                continue
            args = (folder / 'cmdline').read_bytes().split(b'\0')
            if b'--otg' in args:
                sessions.append(int(folder.name))
        except (OSError, ValueError):
            continue
    return sessions


def cursor_state_file():
    return Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid()))) / 'steel-phone-cursor'


def hide_cursor():
    marker = cursor_state_file()
    if not marker.exists():
        option = json.loads(run('hyprctl', 'getoption', 'cursor:invisible', '-j').stdout)
        marker.write_text('1' if option.get('int', option.get('bool', False)) else '0')
        marker.chmod(0o600)
    run('hyprctl', 'dispatch', 'hl.config({cursor={invisible=true}})')


def restore_cursor():
    marker = cursor_state_file()
    if marker.exists():
        value = 'true' if marker.read_text() == '1' else 'false'
        run('hyprctl', 'dispatch', 'hl.config({cursor={invisible=' + value + '}})')
        marker.unlink(missing_ok=True)


def stop(restore_visibility=True):
    # Restore focus before destroying the invisible input surface.
    try:
        current = json.loads(run('hyprctl', 'activewindow', '-j').stdout or '{}')
        if current.get('title') == 'Phone OTG' and current.get('class') == 'scrcpy':
            runtime = Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid())))
            address, position = (runtime / 'steel-phone-focus').read_text().splitlines()[:2]
            x, y = map(int, position.split())
            run('hyprctl', 'dispatch', f'hl.dsp.cursor.move({{x={x},y={y}}})')
            if any(c['address'] == address for c in json.loads(run('hyprctl', 'clients', '-j').stdout)):
                run('hyprctl', 'dispatch', 'hl.dsp.focus({window="address:' + address + '"})')
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    run('systemctl', '--user', 'stop', UNIT)
    for pid in manual_sessions():
        try:
            # Stable process handle avoids signaling a reused PID.
            with os.fdopen(os.pidfd_open(pid), 'rb') as handle:
                signal.pidfd_send_signal(handle.fileno(), signal.SIGTERM)
        except ProcessLookupError:
            continue
    if restore_visibility:
        restore_cursor()


def start():
    executable = shutil.which('scrcpy')
    if not executable:
        raise RuntimeError('Install scrcpy to use USB phone control.')
    runtime = Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid())))
    pointer_socket = Path(os.environ.get('YDOTOOL_SOCKET', str(runtime / '.ydotool_socket')))
    if not shutil.which('ydotool') or not pointer_socket.exists():
        raise RuntimeError('Start the ydotool user service to enable automatic USB pointer handoff.')
    hide_cursor()
    previous = json.loads(run('hyprctl', 'activewindow', '-j').stdout or '{}')
    cursor = json.loads(run('hyprctl', 'cursorpos', '-j').stdout)
    context = runtime / 'steel-phone-focus'
    context.write_text(previous.get('address', '') + '\n' + str(cursor['x']) + ' ' + str(cursor['y']) + '\n')
    context.chmod(0o600)
    command = ['systemd-run', '--user', '--quiet', '--collect', '--service-type=exec',
               '--unit=' + UNIT, '--description=USB phone keyboard and mouse',
               '--property=PartOf=graphical-session.target', '--property=TimeoutStopSec=5s']
    state = runtime / 'steel-phone-capture-state'
    state.unlink(missing_ok=True)
    command += ['--setenv=LD_PRELOAD=' + str(capture_library()), '--setenv=STEEL_PHONE_CAPTURE_STATE=' + str(state)]
    for name in ('WAYLAND_DISPLAY', 'DISPLAY', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS',
                 'HYPRLAND_INSTANCE_SIGNATURE', 'ANDROID_SERIAL'):
        if os.environ.get(name):
            command.append('--setenv=' + name + '=' + os.environ[name])
    if os.environ.get('WAYLAND_DISPLAY'):
        command.append('--setenv=SDL_VIDEO_DRIVER=wayland')
    command += [executable, '--otg', '--window-title=Phone OTG',
                '--window-width=16', '--window-height=16', '--window-borderless']
    result = run(*command)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or 'Could not start USB phone control.')
    # A missing/unavailable USB device makes scrcpy exit immediately. No permanent watcher.
    if not active():
        raise RuntimeError('USB phone control could not start. Check the cable and device; details in the session journal.')
    pid = int(run('systemctl', '--user', 'show', UNIT, '-p', 'MainPID', '--value').stdout)
    window = None
    for _ in range(20):
        window = next((c for c in json.loads(run('hyprctl', 'clients', '-j').stdout) if c['pid'] == pid), None)
        if window:
            break
        time.sleep(.05)
    if not window:
        stop()
        raise RuntimeError('Phone control window did not become ready.')
    def dispatch(expression):
        result = run('hyprctl', 'dispatch', expression)
        if result.returncode or result.stdout.strip() != 'ok':
            raise RuntimeError(result.stdout or result.stderr)
    if previous.get('workspace', {}).get('id', 0) > 0:
        dispatch('hl.dsp.window.move({workspace=' + str(previous['workspace']['id']) +
                 ',follow=false,window="address:' + window['address'] + '"})')
    # Enter the invisible surface. The SDL adapter sets capture ON at focus
    # gain, rather than toggling an unknown state or forwarding an Android click.
    if previous.get('address'):
        dispatch('hl.dsp.focus({window="address:' + previous['address'] + '"})')
        time.sleep(.08)
    x, y = window['at']
    dispatch(f'hl.dsp.cursor.move({{x={x+8},y={y+8}}})')
    dispatch('hl.dsp.focus({window="address:' + window['address'] + '"})')
    # A compositor warp changes coordinates but does not deliver pointer enter
    # to SDL. One relative input event completes Wayland's lock immediately.
    result = run('ydotool', 'mousemove', '1', '0', env=dict(os.environ, YDOTOOL_SOCKET=str(pointer_socket)))
    if result.returncode:
        stop()
        raise RuntimeError('Could not complete the phone pointer handoff.')
    for _ in range(30):
        if state.exists() and state.read_text() == '1':
            break
        time.sleep(.05)
    else:
        stop()
        raise RuntimeError('Phone input capture did not activate.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('toggle', 'start', 'stop', 'status'))
    action = parser.parse_args().action
    runtime = Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid())))
    with (runtime / 'steel-phone-control.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        running = active() or bool(manual_sessions())
        if action == 'status':
            print('active' if running else 'inactive')
        elif action == 'stop' or (action == 'toggle' and running):
            stop()
        elif action == 'start' or not running:
            if running:
                stop(restore_visibility=False)
            start()


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        restore_cursor()
        print(error, file=sys.stderr)
        sys.exit(1)
