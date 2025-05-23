import subprocess
import os

from typing import Literal

from utils import logger

log = logger.Logger("bmp")


def start_gobmp(lab_path, dump: Literal["kafka", "console"], bmp_port, kafka_server=None):
    gobmp_path = os.path.join(lab_path, 'bin', 'gobmp')

    if not os.path.isfile(gobmp_path):
        log.error(f"gobmp not found at {gobmp_path}")
        raise FileNotFoundError(f"gobmp not found at {gobmp_path}")

    log.info(f"Starting gobmp at {gobmp_path}...")

    cmd = [gobmp_path, f"--dump={dump}", f"--source-port={bmp_port}"]

    if dump == "kafka":
        if kafka_server is None:
            raise Exception("kafka settings required for kafka dump")
        cmd.append(f"--kafka-server={kafka_server}")

    proc = subprocess.Popen(
        cmd,
        cwd=lab_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # 实时读取 gobmp 输出
    for line in proc.stdout:
        log.info(line.strip())

    proc.wait()

    if proc.returncode != 0:
        log.error(f"gobmp exited with code {proc.returncode}")
    else:
        log.info("gobmp finished successfully.")