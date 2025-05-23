from kafka import KafkaConsumer, errors as kafka_errors
import time
import threading
import json
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__)
CORS(app)  # 跨域支持，前后端分离必须
socketio = SocketIO(app, cors_allowed_origins="*")

def consume_kafka():
    start_time = time.time()
    timeout = 60  # 最多重连 60 秒
    consumer = None

    while True:
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=["localhost:9092"],
                auto_offset_reset="latest",
                group_id="topo-monitor",
                value_deserializer=lambda m: json.loads(m.decode("utf-8"))
            )
            consumer.subscribe(pattern="gobmp.*")
            print("✅ Kafka connected, start consuming...")
            break  # 成功连接，跳出循环

        except kafka_errors.NoBrokersAvailable:
            print(f"⚠️ Kafka not available, retrying... ({int(time.time() - start_time)}s)")
            if time.time() - start_time > timeout:
                print("❌ Kafka connection timeout. Giving up.")
                return
            time.sleep(5)

    # 消费循环
    for msg in consumer:
        data = {
            "topic": msg.topic,
            "payload": msg.value
        }
        print(f"📩 New message on {msg.topic}")
        socketio.emit("new_message", data)


def flask_main():
    threading.Thread(target=consume_kafka, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=8080)
