import subprocess
import time
import os
import uuid

from utils import logger

log = logger.Logger("Kafka-Launcher")

KAFKA_IMAGE = "apache/kafka:3.8.0"
KAFKA_PORT = 9092
ZOOKEEPER_PORT = 2181

def run_command(cmd):
    """执行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log.error(f"Command failed: {cmd}")
        log.error(f"stderr: {e.stderr}")
        return None

def is_container_running(name):
    """检查容器是否已运行"""
    cmd = f"docker ps --filter 'name={name}' --format '{{{{.Names}}}}'"
    output = run_command(cmd)
    return output == name

def start_kafka(lab_id):
    KAFKA_CONTAINER_NAME= str(lab_id) + "-kafka"
    if is_container_running(KAFKA_CONTAINER_NAME):
        log.info(f"Kafka container '{KAFKA_CONTAINER_NAME}' is already running.")
        return

    log.info(f"Starting Kafka container '{KAFKA_CONTAINER_NAME}'...")

    cmd = (
        f"docker run -d --name {KAFKA_CONTAINER_NAME} "
        f"-p {KAFKA_PORT}:9092 "
        f"{KAFKA_IMAGE}"
    )

    result = run_command(cmd)
    if result:
        log.info(f"Kafka container started successfully: {result}")
    else:
        log.error("Failed to start Kafka container.")

def stop_kafka(lab_id):
    KAFKA_CONTAINER_NAME= str(lab_id) + "-kafka"
    log.info("Stopping Kafka container...")
    cmd = f"docker stop {KAFKA_CONTAINER_NAME} && docker rm {KAFKA_CONTAINER_NAME}"
    run_command(cmd)
    log.info("Kafka container stopped.")

def start_kafka_loop(lab_id):
    """阻塞保持，让守护进程接管"""
    start_kafka(lab_id=lab_id)
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        stop_kafka(lab_id=lab_id)

if __name__ == "__main__":
    start_kafka_loop(lab_id=uuid.uuid4())
