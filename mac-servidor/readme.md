## Para que nos sirve?
usa el entorno de ia local levantado con oMLX en el macbook

- Se debe tener oMLX instalado
- Debe tener un entorno virtual con python3.12
- Copiar el archivo settings.json dentro de ~/.omlx/
- Ejecutar el comando de establecer 28GB de ram para la gpu en macos (sudo sysctl iogpu.wired_limit_mb=28672)
- Ejecutar el modelo (omlx serve --host 0.0.0.0 --port 8080)

## nomic-ai/nomic-embed-text-v1.5
Nos sirve para poder ser el intermediario de embeddings entre opencode y el server, con esto ahorramos tokens y optimizamos las consultas del usuario
- brew install ollama
- OLLAMA_HOST="0.0.0.0:11434" OLLAMA_FLASH_ATTENTION="1" OLLAMA_KV_CACHE_TYPE="q8_0" /opt/homebrew/opt/ollama/bin/ollama serve (Primera terminal)
- ollama pull nomic-embed-text (Segunda terminal)
- ssh -L 11434:localhost:11434 servidor@192.168.2.138 (crear puente desde kali a macbook)

### en Opencode colocar esto dentro del mcp de index:
- OLLAMA_HOST=0.0.0.0:11434 ollama serve
