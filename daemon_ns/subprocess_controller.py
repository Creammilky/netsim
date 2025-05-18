import multiprocessing
import time
import signal
import logging
import sys
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

running = True
processes = []

def component_worker(name):
    while True:
        logging.info(f"Component {name} is running...")
        time.sleep(5)

def start_component(name):
    p = multiprocessing.Process(target=component_worker, args=(name,))
    p.start()
    processes.append(p)
    logging.info(f"Started component: {name} (PID: {p.pid})")

def stop_all_components():
    for p in processes:
        logging.info(f"Stopping component PID: {p.pid}")
        p.terminate()
        p.join()

def signal_handler(sig, frame):
    global running
    logging.info("Shutdown signal received.")
    running = False
    stop_all_components()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    start_component("A")
    start_component("B")
    start_component("C")

    while running:
        time.sleep(1)
