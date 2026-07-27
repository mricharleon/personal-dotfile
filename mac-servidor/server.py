from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI()

print("Cargando modelo ligero bge-small-en-v1.5...")
# Cambiamos nomic por bge-small
model = SentenceTransformer("BAAI/bge-small-en-v1.5")

class Item(BaseModel):
    input: str | list[str]

@app.post("/v1/embeddings")
async def create_embedding(data: Item):
    texts = [data.input] if isinstance(data.input, str) else data.input
    
    # bge-small procesa el texto directo sin prefijos raros
    vectors = model.encode(texts, convert_to_numpy=True)

    return {
        "object": "list",
        "data": [
            {"object": "embedding", "embedding": vec.tolist(), "index": i}
            for i, vec in enumerate(vectors)
        ]
    }
