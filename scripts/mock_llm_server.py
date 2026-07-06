# scripts/mock_llm_server.py
# Mock vLLM server để test integration points khi Kaggle chưa sẵn sàng
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/v1/models")
def models():
    return {"data": [{"id": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4"}]}

@app.post("/v1/chat/completions")
def chat(data: dict):
    prompt = data["messages"][-1]["content"]
    return {
        "choices": [{"message": {"content": f"[MOCK] Response to: {prompt[:50]}... The AI platform integrates Kafka, Prefect, Delta Lake, Qdrant, and vLLM for end-to-end ML workflows."}}],
        "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4"
    }

@app.post("/v1/embeddings")
def embeddings(data: dict):
    import random
    texts = data["input"]
    emb_list = [[random.random() for _ in range(384)] for _ in texts]
    return {"data": [{"embedding": e, "index": i} for i, e in enumerate(emb_list)]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
