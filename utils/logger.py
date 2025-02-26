import configparser
from dotenv import load_dotenv
import logging
import os
from datetime import datetime

load_dotenv()
LOGS_PATH = os.getenv("LOGS_PATH")
TERMINAL_LEVEL = os.getenv("TERMINAL_LEVEL")
FILE_LEVEL = os.getenv("FILE_LEVEL")

# current_dir = os.pardir
# config = configparser.ConfigParser()
# config.read(current_dir + '/settings.ini')
# LOGS_PATH = config.get('Log', 'path')

class Logger:
    create_time: str = None
    log_from: str = None
    log_to: str = None
    log_level: str = None

    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
        self.log_from = logger_name
        self.logger.setLevel(logging.DEBUG)
        self.create_time = Logger.current()
        self.logger_file_name = '/%s.log' % self.create_time  # self.create_time里面有冒号，Windows文件名不支持冒号
        self.logger_file_path = LOGS_PATH
        # 创建文件处理器
        file_handler = logging.FileHandler(self.logger_file_path + self.logger_file_name)
        file_handler.setLevel(logging.INFO)
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # 将格式化器添加到处理器中
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        # 将处理器添加到 Logger 对象中
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    @staticmethod
    def current() -> str:
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H_%M_%S")

    def debug(self, dbg_msg):
        self.logger.debug(msg= f"[{self.log_from}]: {dbg_msg}")

    def info(self, info_msg):
        self.logger.info(msg= f"[{self.log_from}]: {info_msg}")

    def warning(self, warn_msg):
        self.logger.info(msg= f"[{self.log_from}]: {warn_msg}")

    def error(self, err_msg):
        self.logger.error(msg= f"[{self.log_from}]: {err_msg}")

    def critical(self, crt_msg):
        self.logger.critical(msg= f"[{self.log_from}]: {crt_msg}")