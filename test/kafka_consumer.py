from kafka import KafkaConsumer
import json

KAFKA_SERVERS = ['localhost:9092']

def consume_all_topics():
    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_SERVERS,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='all-topics-consumer',
        value_deserializer=lambda m: m.decode('utf-8')
    )

    # 订阅所有 topic（用正则匹配）
    consumer.subscribe(pattern=".*")

    print("Subscribed to all topics.")

    try:
        for message in consumer:
            # Can be used for verify
            print(f"Topic: {message.topic}, Partition: {message.partition}, Offset: {message.offset}")
            # Can be used for generating network topology
            print(print(json.dumps(json.loads(message.value), indent=4))
)
            # ===Separate===. no need for real consuming
            print("=" * 50)

    except KeyboardInterrupt:
        print("Stopped by user.")

    finally:
        consumer.close()
        print("Consumer closed.")

if __name__ == "__main__":
    consume_all_topics()
