import configparser
from dotenv import load_dotenv
import logging
import os
from datetime import datetime
from colorama import init, Fore

# 初始化 colorama，支持 Windows 终端颜色
init(autoreset=True)

load_dotenv()
LOGS_PATH = os.getenv("LOGS_PATH", "./logs")
TERMINAL_LEVEL = os.getenv("TERMINAL_LEVEL", "INFO").upper()
FILE_LEVEL = os.getenv("FILE_LEVEL", "INFO").upper()

# 定义日志颜色
LOG_COLORS = {
    "DEBUG": Fore.BLUE,
    "INFO": Fore.GREEN,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.MAGENTA,
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        log_color = LOG_COLORS.get(record.levelname, Fore.WHITE)
        record.msg = f"{log_color}{record.msg}"
        return super().format(record)

class Logger:
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        self.create_time = Logger.current()
        self.logger_file_name = f"/{self.create_time}.log"
        self.logger_file_path = LOGS_PATH
        os.makedirs(self.logger_file_path, exist_ok=True)  # 确保日志目录存在

        # 创建文件处理器
        file_handler = logging.FileHandler(self.logger_file_path + self.logger_file_name)
        file_handler.setLevel(getattr(logging, FILE_LEVEL, logging.INFO))
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, TERMINAL_LEVEL, logging.INFO))
        console_formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        # 将处理器添加到 Logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    @staticmethod
    def current() -> str:
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H_%M_%S")

    def debug(self, dbg_msg):
        self.logger.debug(f"[{self.logger.name}]: {dbg_msg}")

    def info(self, info_msg):
        self.logger.info(f"[{self.logger.name}]: {info_msg}")

    def warning(self, warn_msg):
        self.logger.warning(f"[{self.logger.name}]: {warn_msg}")

    def error(self, err_msg):
        self.logger.error(f"[{self.logger.name}]: {err_msg}")

    def critical(self, crt_msg):
        self.logger.critical(f"[{self.logger.name}]: {crt_msg}")
