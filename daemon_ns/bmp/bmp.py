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

    if dump == "kafka":
        if kafka_server is None:
            raise Exception("kafka settings required for kafka dump")
        else:
            result = subprocess.run(
                [gobmp_path, f"--dump={dump}", f"--source-port={bmp_port}", f"--kafka-server={kafka_server}"],
                cwd=lab_path,
                capture_output=True,
                text=True
            )
    else:
        proc = subprocess.Popen(
            [gobmp_path, f"--dump={dump}", f"--source-port={bmp_port}"],
            cwd=lab_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in proc.stdout:
            log.info(line.strip())

    log.info(result.stdout)

    if result.returncode != 0:
        log.error(f"gobmp failed: {result.stderr}")
    else:
        log.info("gobmp finished successfully.")