import daemon
import time
import signal
import os
import sys

# 定义守护进程要做的事情
def run():
    logfile = "/tmp/daemon_example.log"
    with open(logfile, "a") as f:
        f.write("Daemon started.\n")

    while True:
        with open(logfile, "a") as f:
            f.write(f"{time.ctime()}\n")
        time.sleep(5)

# 可选：定义退出时的清理函数
def cleanup():
    with open("/tmp/daemon_example.log", "a") as f:
        f.write("Daemon exiting...\n")

def daemon_main():
    # 配置 DaemonContext
    with daemon.DaemonContext(
        stdout=sys.stdout,       # 重定向标准输出
        stderr=sys.stderr,       # 重定向标准错误
        working_directory="/",   # 工作目录
        umask=0o002,             # 文件权限掩码
        signal_map={
            signal.SIGTERM: cleanup,  # 捕捉 SIGTERM 做清理
            signal.SIGHUP: 'terminate'
        }
    ):
        run()

if __name__ == '__main__':
    daemon_main()