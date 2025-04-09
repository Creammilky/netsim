"""
Subscribe to a RIS Live stream and output every message to stdout.

IMPORTANT: this example requires 'websocket-client' for Python 2 or 3.

If you use the 'websockets' package instead (Python 3 only) you will need to change the code because it has a somewhat different API.
"""
import json
import websocket

from dotenv import load_dotenv

from utils.ipv4_utils import is_ipv4, is_ipv6
from utils import logger


# Load environment variables from .env file
load_dotenv()

# Initialize logger
log = logger.Logger("ripelive")

def ripe_filter(datum, ip_type: int = 10, hosts: list = None):
    if hosts is not None:
        result = ripe_host_subfilter(datum, hosts)
        if result is None:
            return None
    if ip_type is not None:
        result = ripe_ip_subfilter(datum, ip_type)
        if result is None:
            return None
    return datum

def ripe_ip_subfilter(datum, ip_type):
    ip_addr = datum.get("peer")
    if ip_type==4:
        if is_ipv4(ip_addr) is True:
            return datum
        else:
            return None
    if ip_type==6:
        if is_ipv6(ip_addr) is True:
            return datum
        else:
            return None
    if ip_type==10:
        return datum
    else:
        log.error(f"Unsupported IP type: {ip_type}")
        raise Exception(f"Unsupported IP type: {ip_type}")

def ripe_host_subfilter(datum, hosts):
    ripe_hosts = ["ALL", "all" ,"rrc00.ripe.net", "rrc01.ripe.net"
        , "rrc03.ripe.net", "rrc04.ripe.net", "rrc05.ripe.net", "rrc06.ripe.net", "rrc07.ripe.net"
        , "rrc10.ripe.net", "rrc11.ripe.net", "rrc12.ripe.net", "rrc13.ripe.net", "rrc14.ripe.net", "rrc15.ripe.net"
        , "rrc16.ripe.net"
        , "rrc18.ripe.net", "rrc19.ripe.net", "rrc20.ripe.net", "rrc21.ripe.net"
        , "rrc22.ripe.net", "rrc23.ripe.net", "rrc24.ripe.net", "rrc25.ripe.net", "rrc26.ripe.net"]

    host_filter = []

    for host in hosts:
        if host not in ripe_hosts:
            log.warning("Skipping filter host:{}".format(host))
        else:
            log.debug("Apply filter host:{}".format(host))
            host_filter.append(host)

    host = datum.get("host")
    if host in host_filter:
        return datum
    else:
        return None

def ripe_msg_type_subfilter(datum, msg_type):
    msg_types = ["UPDATE", "OPEN", "NOTIFICATION","KEEPALIVE"]

    message_type_filter = []

    for _type in msg_type:
        if _type not in msg_types:
            log.warning("Skipping filter host:{}".format(_type))
        else:
            log.debug("Apply filter host:{}".format(_type))
            message_type_filter.append(_type)

    _type = datum.get("type")
    if _type in message_type_filter:
        return datum
    else:
        return None

ws = websocket.WebSocket()
ws.connect("wss://ris-live.ripe.net/v1/ws/?client=py-example-1")
params = {
    "moreSpecific": True,
    "host": "",
    "socketOptions": {
        "includeRaw": True
    }
}
ws.send(json.dumps({
        "type": "ris_subscribe",
        "data": params
}))
for data in ws:
    parsed = json.loads(data)
    print(parsed)
    data = {
        "peer": parsed["data"].get("peer"),
        "peer_asn": parsed["data"].get("peer_asn"),
        "host": parsed["data"].get("host"),
        "type": parsed["data"].get("type"),
        "path": parsed["data"].get("path"),
        "origin": parsed["data"].get("origin"),
        "announcements": parsed["data"].get("announcements", []),  # 如果没有，默认空列表
        "withdrawals": parsed["data"].get("withdrawals", []),  # 如果没有，默认空列表
    }
    # result = ripe_filter(data, 4, ["rrc00.ripe.net", "rrc03.ripe.net", "rrc04.ripe.net"])
    # if result is not None:
    #     print(result)

