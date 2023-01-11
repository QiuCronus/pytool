import os
import sys
import subprocess

__all__ = ["execute"]


def _patch_windows():
    SUBPROCESS_FLAG = 0
    if sys.platform.startswith("win"):
        # Don't display the windows GPF dialog if the invoked program dies.
        try:
            SUBPROCESS_FLAG = subprocess.CREATE_NO_WINDOW
        except AttributeError:
            import ctypes

            SEM_NOGPFAULTERRORBOX = 0x0002
            ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX)
            SUBPROCESS_FLAG = 0x8000000
    return SUBPROCESS_FLAG


def execute(cmd):
    if sys.version_info >= (3, 7):
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=_patch_windows(),
            encoding="utf8",
            text=True,
            shell=True,
            env=os.environ.copy(),
        )
    else:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=_patch_windows(),
            encoding="utf8",
            shell=True,
            env=os.environ.copy(),
        )
    proc.wait()
    stdout = "\n".join(proc.stdout.readlines()) or None
    stderr = "\n".join(proc.stderr.readlines()) or None
    return proc.returncode, stdout, stderr
