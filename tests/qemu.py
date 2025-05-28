from os import path
from typing import Tuple, Optional

from utils import run_command, dirpath


def run_qemu(asm_text: str) -> Optional[str]:
    base_path = dirpath(__file__)
    tb_path = path.join(base_path, "cpu_testbench")

    with open(path.join(tb_path, "kernel.s"), "w") as f:
        f.write(asm_text)

    status, stdout, stderr = run_command(
        "make -s qemu",
        timeout=1, cwd=tb_path
    )
    stderr = stderr.strip()
    if len(stderr) > 0:
        print("£" * 5 + "stderr" + "£" * 5)
        print(stderr)
    return stdout + stderr
