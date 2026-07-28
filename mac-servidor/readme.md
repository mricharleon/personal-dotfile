## Para que nos sirve?
usa el entorno de ia local levantado con oMLX en el macbook

- Se debe tener oMLX instalado
- Debe tener un entorno virtual con python3.12
- Copiar el archivo settings.json dentro de ~/.omlx/
- Ejecutar el comando de establecer 28.5GB de ram para la gpu en macos (sudo sysctl iogpu.wired_limit_mb=29184)
- Ejecutar el modelo (omlx serve --host 0.0.0.0 --port 8080 --initial-cache-blocks 40)

## nomic-ai/nomic-embed-text-v1.5
Nos sirve para poder ser el intermediario de embeddings entre opencode y el server, con esto ahorramos tokens y optimizamos las consultas del usuario
- brew install ollama
- OLLAMA_HOST="0.0.0.0:11434" OLLAMA_FLASH_ATTENTION="1" OLLAMA_KV_CACHE_TYPE="q8_0" /opt/homebrew/opt/ollama/bin/ollama serve (Primera terminal)
- ollama pull nomic-embed-text (Solo para descargar el modelo la primera vez)
- ssh -L 11434:localhost:11434 servidor@192.168.2.138 (crear puente desde kali a macbook)

### en Opencode colocar esto dentro del mcp de index:
- OLLAMA_HOST=0.0.0.0:11434 ollama serve


# Guía de Configuración de Memoria y Contexto en oMLX

Esta documentación explica la matemática detrás de la selección de bloques de caché KV en **oMLX** para el modelo `Qwen3.6-35B-A3B` en un equipo Apple Silicon de 32 GB de RAM, y cómo recalcular los parámetros en caso de modificar la ventana de contexto.

---

## 1. ¿Por qué elegimos exactamente 40 bloques para 82k tokens?

La gestión de contexto en oMLX utiliza una técnica de atención paginada (**PagedAttention**). En lugar de asignar memoria token por token de forma dinámica, la memoria KV se reserva en "páginas" o "bloques" fijos.

### La regla de cálculo del bloque
Para modelos híbridos/MoE como Qwen, oMLX ajusta automáticamente el tamaño de bloque a **2048 tokens por bloque** (`block_size=2048`) para optimizar las operaciones de la GPU Metal.

### La ecuación:
$$\text{Bloques Necesarios} = \frac{\text{Ventana de Contexto Deseada (tokens)}}{\text{Tamaño de Bloque (tokens/bloque)}}$$

Aplicando nuestra ventana de **81,920 tokens (82k)**:

$$\text{Bloques} = \frac{81920 \text{ tokens}}{2048 \text{ tokens/bloque}} = 40 \text{ bloques}$$

> **Nota importante:** Si usamos el valor antiguo de 640 bloques con el nuevo `block_size=2048`, oMLX intentaría reservar $640 \times 2048 = 1,310,720\text{ tokens}$ (~1.3 millones de tokens), saturando los 32 GB de RAM y provocando la cancelación del proceso por sobrepresión de memoria (*Memory Enforcer Abort*).

---

## 2. Parámetros de Arranque Recomendados

Para un sistema con **32 GB de RAM Unificada**, la línea de comando ideal es:

```bash
omlx serve --host 0.0.0.0 --port 8080 --initial-cache-blocks 40
