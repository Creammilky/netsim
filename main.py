# Builtins
import functools
import os
import signal
import uuid
from time import sleep

# Packages(site)
from dotenv import load_dotenv
import networkx as nx

# Internal Files
from api.lab_manage import topology, create_lab
from daemon_ns.bmp import bmp
from daemon_ns.clab import clab
from utils import logger, xml_parser, graph_utils

# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("main")

# Fetch environment variables
ROUTER_IMAGE = os.getenv("ROUTER_IMAGE")
LABS_PATH = os.getenv("LABS_PATH")
FRR_VERSION = os.getenv("FRR_VERSION")
if not ROUTER_IMAGE or not LABS_PATH:
    log.error("Required environment variables ROUTER_IMAGE or LABS_PATH are missing!")
    raise EnvironmentError("Required environment variables are missing!")

# Usage example
if __name__ == "__main__":

    LAB_ID = uuid.uuid4()
    CURRENT_LAB_PATH = os.path.join(LABS_PATH, str(LAB_ID))

    # 注册信号处理器，绑定 lab_path 参数
    handler = functools.partial(clab.signal_handler, CURRENT_LAB_PATH)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    parser = xml_parser.GraphParser("test/route-xmls/route_2.xml")
    parser.parse()
    G_xml = parser.get_networkx()
    # G_updates = topology.bgp_to_networkx('test/ripe_output.txt')

    create_lab.create_lab_instance(G=G_xml, lab_path=CURRENT_LAB_PATH, frr_version=FRR_VERSION)
    clab.deploy_lab(CURRENT_LAB_PATH)
    from daemon_ns.netsim_daemon import start_daemon
    start_daemon(lab_path=CURRENT_LAB_PATH, lab_id=LAB_ID, is_test=True)

    try:
        # bmp.start_gobmp(lab_path=CURRENT_LAB_PATH, dump="kafka", bmp_port="5000", kafka_server="0.0.0.0:9092")
        while True:
            log.debug("is running")
            sleep(3)
    except Exception as e:
        log.error(f"BMP Socket error caught in main process {e}")
        clab.destroy_lab(CURRENT_LAB_PATH)
