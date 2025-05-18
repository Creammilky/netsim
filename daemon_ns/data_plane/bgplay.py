import asyncio
import websockets
import json
import time

def convert_gobmp_to_bgplay(msg):
    as_path = [
        {"owner": "Unknown", "as_number": str(asn)}
        for asn in msg["base_attrs"]["as_path"]
    ]

    bgplay_event = {
        "type": "A",
        "timestamp": int(time.time()),
        "path": as_path,
        "source": {
            "as_number": str(msg["peer_asn"]),
            "rrc": "simulator",
            "id": f"simulator-{msg['peer_ip']}",
            "ip": msg["peer_ip"]
        },
        "target": {
            "prefix": f"{msg['prefix']}/{msg['prefix_len']}"
        },
        "community": ""  # 如果有 community 这里拼上
    }

    return bgplay_event


def elem2bgplay(rec, elem):
    msg = {
        'type': elem.type,
        'timestamp': elem.time,
        'target': {
            'prefix': elem.fields['prefix'],
        },
        'source': {
            'as_number': elem.peer_asn,
            'ip': elem.peer_address,
            'project': rec.project,
            'collector': rec.collector,
            'id': f"{rec.project}-{rec.collector}-{elem.peer_asn}-{elem.peer_address}"
        }
    }
    if elem.type == 'A':
        msg['path'] = [
            {'owner': str(asn), 'as_number': str(asn)}
            for asn in elem.fields['as-path'].split()
        ]
    return msg

connected_clients = set()

# 定义要推送的 JSON 消息，符合 bgplayjs 要求的格式
def make_message():
    return {
        "type": "A",
        "timestamp": int(time.time()),
        "path": [
            {"owner": " AS Test A", "as_number": "65001"},
            {"owner": " AS Test B", "as_number": "65002"}
        ],
        "source": {
            "as_number": "65001",
            "rrc": "test-rrc",
            "id": "test-65001",
            "ip": "192.168.0.1"
        },
        "target": {
            "prefix": "209.212.8.0/24"
        },
        "community": "65001:100 65002:200"
    }


# 处理连接 — 必须 websocket, path 两个参数
async def handler(websocket):
    print(f"客户端连接: {websocket.remote_address}")
    connected_clients.add(websocket)

    try:
        while True:
            await asyncio.sleep(5)
            message = json.dumps(make_message())
            await websocket.send(message)
            print(f"推送消息: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"客户端断开: {websocket.remote_address}")
    finally:
        connected_clients.remove(websocket)



# 启动 WebSocket 服务
async def main():
    server = await websockets.serve(handler, "0.0.0.0", 6789)
    print("WebSocket 服务启动，监听 ws://0.0.0.0:6789")
    await server.wait_closed()  # 等待服务关闭


if __name__ == "__main__":
    asyncio.run(main())