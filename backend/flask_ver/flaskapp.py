from flask import Flask, render_template
from flask_socketio import SocketIO
from kafka import KafkaConsumer
import threading, json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

def consume_kafka():
    consumer = KafkaConsumer(
        bootstrap_servers=["localhost:9092"],
        auto_offset_reset="latest",
        group_id="topo-monitor",
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )
    consumer.subscribe(pattern="gobmp.*")

    for msg in consumer:
        data = {
            "topic": msg.topic,
            "payload": msg.value
        }
        socketio.emit("new_message", data)

@app.route("/")
def index():
    return render_template("topo.html")

if __name__ == "__main__":
    threading.Thread(target=consume_kafka, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=8080)
