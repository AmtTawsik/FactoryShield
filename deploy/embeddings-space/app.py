import gradio as gr
import spaces
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-small"

model = SentenceTransformer(MODEL_NAME, device="cuda")
api = FastAPI()


class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str = MODEL_NAME
    encoding_format: str = "float"


@spaces.GPU(duration=30)
def embed(texts: list[str]) -> list[list[float]]:
    return model.encode(texts, batch_size=32, normalize_embeddings=True).tolist()


@api.post("/v1/embeddings")
def embeddings(request: EmbeddingRequest):
    texts = [request.input] if isinstance(request.input, str) else request.input
    data = [{"object": "embedding", "index": i, "embedding": vector} for i, vector in enumerate(embed(texts))]
    return {"object": "list", "model": MODEL_NAME, "data": data, "usage": {"prompt_tokens": 0, "total_tokens": 0}}


@api.get("/health")
def health():
    return {"status": "ok"}


def preview(text: str) -> dict:
    vector = embed([text])[0]
    return {"dimensions": len(vector), "first_values": vector[:5]}


demo = gr.Interface(fn=preview, inputs=gr.Textbox(label="Text"), outputs=gr.JSON(), title="FactoryShield embeddings")
app = gr.mount_gradio_app(api, demo, path="/", ssr_mode=False)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
