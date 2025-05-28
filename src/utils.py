import codecs
import os
import re
import shlex
import signal
import subprocess
from os.path import dirname, realpath
from typing import Optional, Tuple, List, Type


def dirpath(f):
    return dirname(realpath(f))


def run_command(
        command: str,
        timeout: float,
        cwd: Optional[str] = None
) -> Tuple[bool, str, str]:
    process_env = os.environ.copy()
    try:
        proc = subprocess.Popen(
            shlex.split(command),
            cwd=cwd,
            env=process_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True
        )
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

        stdout = proc.stdout.read()
        stderr = proc.stderr.read()
        stderr = re.sub(r"qemu-system-riscv64.*\n", "", stderr)
        return proc.returncode == 0, stdout, stderr

    except Exception as e:
        if 'proc' in locals() and proc.poll() is None:
            proc.kill()
        raise e


def string_escape(s: str) -> str:
    return codecs.escape_encode(s.encode("ascii"))[0].decode("ascii")


def string_unescape(s: str) -> str:
    return codecs.escape_decode(s)[0].decode("ascii")


def class_hierarchy(x) -> List[Type]:
    res = [x.__class__]
    while (base := res[-1].__base__) is not None: res.append(base)
    return res


def str_class_hierarchy(x) -> List[str]:
    return [i.__name__ for i in class_hierarchy(x)]
