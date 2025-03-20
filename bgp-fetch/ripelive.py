"""
Subscribe to a RIS Live stream and output every message to stdout.

IMPORTANT: this example requires 'websocket-client' for Python 2 or 3.

If you use the 'websockets' package instead (Python 3 only) you will need to change the code because it has a somewhat different API.
"""
import json
import websocket
from utils.ipv4_utils import is_ipv4

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
    if is_ipv4(parsed["data"]["peer"]):
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

        print(data)