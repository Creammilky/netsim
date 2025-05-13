import functools
import subprocess
import signal
import sys

from dotenv import load_dotenv

from utils import logger, xml_parser, graph_utils

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("daemon-lab")


def deploy_lab(lab_path):
    result = subprocess.run(
        ['sudo', 'clab', 'deploy'],
        cwd=lab_path,
        capture_output=True,
        text=True
    )
    log.info(result.stdout)
    if result.returncode != 0:
        log.error(f"Deploy failed: {result.stderr}")
        sys.exit(1)

def destroy_lab(lab_path):
    result = subprocess.run(
        ['sudo', 'clab', 'destroy'],
        cwd=lab_path,
        capture_output=True,
        text=True
    )
    log.info(result.stdout)
    if result.returncode != 0:
        log.error(f"Destroy failed: {result.stderr}")

def signal_handler(lab_path, sig, frame):
    log.info(f"收到信号 {sig}，执行清理")
    destroy_lab(lab_path)
    sys.exit(0)

if __name__ == "__main__":
    lab_path = "./lab"

    # 注册信号处理器，绑定 lab_path 参数
    handler = functools.partial(signal_handler, lab_path)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    deploy_lab(lab_path)

    log.info("程序运行中，按 Ctrl+C 停止")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        log.info("收到键盘中断，退出程序")
        destroy_lab(lab_path)