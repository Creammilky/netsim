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

workers = []
log = logger.Logger("daemon")

def start_worker(name, lab_path, lab_id):
    from utils import logger
    log = logger.Logger("daemon")

    if name == "GO-BMP":
        from daemon_ns.bmp import bmp
        bmp.start_gobmp(lab_path=lab_path, dump="kafka", bmp_port="5000", kafka_server="0.0.0.0:9092")  # 阻塞型，内部自己起子进程或执行任务
    elif name == "FLASK":
        from backend.flask_ver import flaskapp
        flaskapp.flask_main()
    elif name == "KAFKA":
        from daemon_ns.kafka import start_kafka
        start_kafka.start_kafka_loop(lab_id=lab_id)
    else:
        log.error(f"Unknown component: {name}")

    log.info(f"[{name}] Exiting.")


def stop_all_workers():
    log.info("[Daemon] Stopping all workers...")
    for p in workers:
        if p.is_alive():
            p.terminate()
            p.join()
    log.info("[Daemon] All workers stopped.")

def handle_exit(signum, frame, lab_path):
    log.info(f"[Daemon] Received signal {signum}, stopping...")
    stop_all_workers()
    if os.path.exists(os.path.join(lab_path, "daemon.pid")):
        os.remove(os.path.join(lab_path, "daemon.pid"))
    sys.exit(0)

def main(lab_path, lab_id):
    import functools
    signal.signal(signal.SIGINT, functools.partial(handle_exit, lab_path=lab_path))
    signal.signal(signal.SIGTERM, functools.partial(handle_exit, lab_path=lab_path))

    names = ["GO-BMP", "FLASK", "KAFKA"]
    for name in names:
        p = multiprocessing.Process(target=start_worker, args=(name,lab_path, lab_id))
        p.start()
        workers.append(p)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_all_workers()

def start_daemon(lab_path, lab_id, is_test):
    with Daemonizer() as (is_setup, daemonizer):
        if is_setup:
            log.info("[Daemon] Preparing to start...")
            log.info(f"[Daemon] Daemon will started by , {os.getpid()}:")

        is_parent, = daemonizer(os.path.join(lab_path, "daemon.pid"))

        # kill parent to make daemon running as an independent process
        if is_parent:
            log.info(f"[Daemon] Daemon started:")
            if not is_test:
                sys.exit(0) # what would happen if I canceled this statement

        main(lab_path=lab_path, lab_id=lab_id) # this contains all function I am gonna run, use multiprocessing to let daemon take them
