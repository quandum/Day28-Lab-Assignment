# Kaggle Notebook - Lab #28: Full Platform Integration Sprint
# Học viên: Trần Mạnh Chánh Quân - 2A202600786
#
# Cách dùng: Copy từng cell (đánh dấu # %% CELL) vào Kaggle Notebook
# Yêu cầu: Bật GPU T4 x2 trong Settings → Accelerator

# %% ----------------------------------------------------------
# CELL 1: Cài đặt dependencies (~2 phút)
# ----------------------------------------------------------
!pip install -q vllm fastapi uvicorn pyngrok mlflow sentence-transformers

# Nếu cài vLLM bị lỗi, thử fallback:
# !pip install transformers==4.46.3 --quiet
# !pip install vllm==0.7.3 --quiet

# %% ----------------------------------------------------------
# CELL 2: Setup ngrok với reserved domain
# ----------------------------------------------------------
import os

NGROK_AUTH_TOKEN = "3F4q4Q84KNSUEhAwHcKXZ8l9pYU_2rNqYepwpDRKW5Wo6ohhM"
VLLM_DOMAIN = "reptile-ancient-putdown.ngrok-free.dev"

from pyngrok import ngrok
ngrok.set_auth_token(NGROK_AUTH_TOKEN)
print("ngrok authenticated ✓")

# %% ----------------------------------------------------------
# CELL 3: Khởi động vLLM server (Single GPU, port 8001)
# ----------------------------------------------------------
import subprocess, threading, time

def run_vllm():
    subprocess.run([
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", "Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
        "--port", "8001",
        "--max-model-len", "4096",
        "--gpu-memory-utilization", "0.5"
    ])

thread = threading.Thread(target=run_vllm, daemon=True)
thread.start()
print("Waiting 60s for vLLM to load model...")
time.sleep(60)
print("vLLM server started ✓")

# %% ----------------------------------------------------------
# CELL 4: Tạo ngrok tunnel cho vLLM (reserved domain)
# ----------------------------------------------------------
tunnel = ngrok.connect(8001, "http", hostname=VLLM_DOMAIN)
vllm_url = tunnel.public_url
print(f"vLLM URL: {vllm_url}")
# Output: https://reptile-ancient-putdown.ngrok-free.dev

# %% ----------------------------------------------------------
# CELL 5: Khởi động Embedding API server (port 8002)
# ----------------------------------------------------------
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import uvicorn, threading

app = FastAPI()
model = SentenceTransformer("BAAI/bge-small-en-v1.5")

@app.post("/embed")
def embed(data: dict):
    texts = data["texts"]
    embeddings = model.encode(texts).tolist()
    return {"embeddings": embeddings}

def run_embed():
    uvicorn.run(app, host="0.0.0.0", port=8002)

threading.Thread(target=run_embed, daemon=True).start()
print("Embedding server started ✓")

# %% ----------------------------------------------------------
# CELL 6: Tạo ngrok tunnel cho Embedding (random URL)
# ----------------------------------------------------------
embed_tunnel = ngrok.connect(8002, "http")
embed_url = embed_tunnel.public_url
print(f"Embedding URL: {embed_url}")
# → Copy URL này vào file .env: EMBED_NGROK_URL=<url này>

# %% ----------------------------------------------------------
# CELL 7: Kiểm tra nhanh
# ----------------------------------------------------------
import requests

# Test vLLM
r = requests.get(f"{vllm_url}/v1/models")
print(f"vLLM models: {r.json()}")

# Test Embedding
r = requests.post(f"{embed_url}/embed", json={"texts": ["hello world"]})
print(f"Embedding test: {len(r.json()['embeddings'][0])} dims")
print("\n=== ALL SERVICES READY ===")
print(f"VLLM_NGROK_URL={vllm_url}")
print(f"EMBED_NGROK_URL={embed_url}")
