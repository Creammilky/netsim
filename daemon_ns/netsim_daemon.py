from daemoniker import Daemonizer, SIGINT, SIGTERM, SignalHandler1
import multiprocessing
import os
import time
import signal
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import logger

PID_FILE = "../test/daemon/mydaemon.pid"
workers = []
log = logger.Logger("daemon")

def start_worker(name):
    from utils import logger  # 保证在子进程内 import，重新初始化 logger
    log = logger.Logger("daemon")
    while True:
        log.info(f"Running, pid: {os.getpid()}")
        time.sleep(3)

def stop_all_workers():
    log.info("[Daemon] Stopping all workers...")
    for p in workers:
        if p.is_alive():
            p.terminate()
            p.join()
    log.info("[Daemon] All workers stopped.")

def handle_exit(signum, frame):
    log.info(f"[Daemon] Received signal {signum}, stopping...")
    stop_all_workers()
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    names = ["Component-A", "Component-B", "Component-C"]
    for name in names:
        p = multiprocessing.Process(target=start_worker, args=(name,))
        p.start()
        workers.append(p)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_all_workers()

with Daemonizer() as (is_setup, daemonizer):
    if is_setup:
        log.info("[Daemon] Preparing to start...")
        log.info(f"[Daemon] Daemon will started by , {os.getpid()}:")

    is_parent, = daemonizer(PID_FILE)

    # kill parent to make daemon running as an independent process
    if is_parent:
        log.info(f"[Daemon] Daemon started:")
        sys.exit(0)

    main() # this contains all function I am gonna run, use multiprocessing to let daemon take them
