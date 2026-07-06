# scripts/05_embed_to_qdrant.py
import requests, os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

EMBED_URL = os.environ["EMBED_NGROK_URL"]
qdrant = QdrantClient(host="localhost", port=6333)

# Dùng vLLM embeddings API (OpenAI-compatible)
def get_embeddings(texts: list[str]) -> list[list[float]]:
    resp = requests.post(f"{EMBED_URL}/v1/embeddings", json={
        "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
        "input": texts
    })
    data = resp.json()
    return [d["embedding"] for d in data["data"]]

# Lấy embedding đầu tiên để xác định kích thước vector
test_emb = get_embeddings(["test"])[0]
vec_size = len(test_emb)
print(f"Vector size: {vec_size}")

# Tạo collection với kích thước phù hợp
qdrant.recreate_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=vec_size, distance=Distance.COSINE)
)

def embed_and_store(records: list[dict]):
    texts = [r["text"] for r in records]
    embeddings = get_embeddings(texts)

    points = [
        PointStruct(id=i, vector=emb, payload=rec)
        for i, (emb, rec) in enumerate(zip(embeddings, records))
    ]
    qdrant.upsert(collection_name="documents", points=points)
    print(f"Integration 5 OK: {len(points)} vectors stored in Qdrant")

# Test với sample data
embed_and_store([
    {"id": "doc_001", "text": "AI platform integration test"},
    {"id": "doc_002", "text": "Kafka to Airflow pipeline"},
])
