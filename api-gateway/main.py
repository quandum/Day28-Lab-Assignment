# api-gateway/main.py
from fastapi import FastAPI, Request, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
import httpx, os, time

app = FastAPI(title="AI Platform API Gateway")
Instrumentator().instrument(app).expose(app)

VLLM_URL = os.environ["VLLM_URL"]
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")

class ChatRequest(BaseModel):
    query: str
    embedding: list[float] = []

@app.post("/api/v1/chat")
async def chat(req: ChatRequest):
    start = time.time()

    # 1. Vector search
    async with httpx.AsyncClient() as client:
        search_resp = await client.post(f"{QDRANT_URL}/collections/documents/points/search", json={
            "vector": req.embedding if req.embedding else [0.0] * 384,
            "limit": 3
        })
        context = search_resp.json().get("result", [])

    # 2. LLM inference
    prompt = f"Context: {context}\n\nQuery: {req.query}"
    async with httpx.AsyncClient(timeout=30) as client:
        llm_resp = await client.post(f"{VLLM_URL}/v1/chat/completions", json={
            "model": "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
            "messages": [{"role": "user", "content": prompt}]
        })

    latency = (time.time() - start) * 1000
    result = llm_resp.json()

    return {
        "answer": result["choices"][0]["message"]["content"],
        "latency_ms": round(latency, 2),
        "model": result["model"]
    }

@app.get("/health")
def health():
    return {"status": "ok"}
