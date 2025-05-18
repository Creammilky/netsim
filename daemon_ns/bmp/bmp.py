import subprocess
import os

from typing import Literal

from utils import logger

log = logger.Logger("bmp")


def start_gobmp(lab_path, dump: Literal["kafka", "console"], port):
    gobmp_path = os.path.join(lab_path, 'bin', 'gobmp')

    if not os.path.isfile(gobmp_path):
        log.error(f"gobmp not found at {gobmp_path}")
        return

    log.info(f"Starting gobmp at {gobmp_path}...")

    result = subprocess.run(
        [gobmp_path, f"--dump={dump}", f"--source-port={port}"],
        cwd=lab_path,
        capture_output=True,
        text=True
    )

    log.info(result.stdout)
    if result.returncode != 0:
        log.error(f"gobmp failed: {result.stderr}")
    else:
        log.info("gobmp finished successfully.")