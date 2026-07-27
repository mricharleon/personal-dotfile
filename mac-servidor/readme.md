## Para que nos sirve?
usa el entorno de ia local levantado con oMLX en el macbook

- Se debe tener oMLX instalado
- Debe tener un entorno virtual con python3.12
- Copiar el archivo settings.json dentro de ~/.omlx/
- Ejecutar el comando de establecer 28GB de ram para la gpu en macos (sudo sysctl iogpu.wired_limit_mb=28672)
- Ejecutar el modelo (omlx serve --host 0.0.0.0 --port 8080)

## nomic-ai/nomic-embed-text-v1.5
Nos sirve para poder ser el intermediario de embeddings entre opencode y el server, con esto ahorramos tokens y optimizamos las consultas del usuario
- pip install mlx-embedding-models
- python -m mlx_embedding_models.embedding --model nomic-ai/nomic-embed-text-v1.5
