# scripts/02_kafka_to_delta_standalone.py
# Integration 2: Kafka → Delta Lake (không dùng Prefect, chạy trực tiếp)
from kafka import KafkaConsumer
import json, os
import pandas as pd
from datetime import datetime

consumer = KafkaConsumer(
    "data.raw",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    consumer_timeout_ms=5000,
    value_deserializer=lambda m: json.loads(m.decode())
)

records = []
for msg in consumer:
    records.append(msg.value)

if records:
    path = "delta-lake/raw"
    os.makedirs(path, exist_ok=True)
    df = pd.DataFrame(records)
    filepath = f"{path}/batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    df.to_parquet(filepath)
    print(f"Consumed {len(records)} records from Kafka")
    print(f"Saved {len(df)} records to {filepath}")
    print("Integration 2 OK: Kafka → Delta Lake")
else:
    print("No records in Kafka. Run 01_ingest_to_kafka.py first!")
