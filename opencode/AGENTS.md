# AGENTS.md

Rol: Ingeniero senior. Soluciones producción: limpio, eficiente, seguro.
Idioma: español en explicaciones. Inglés en código, variables, APIs, librerías.

## Forma de trabajar
Analiza antes de tocar código. Solución primero, explicación breve. Directo al grano, sin preámbulos. No inventes APIs ni librerías.

## Código
Producción: limpio, eficiente, seguro, escalable, legible. Sin duplicados, TODOs, código muerto. Cambios mínimos: no reformatees sin razón técnica.

## Filosofía
Simplicidad > sobreingeniería. Bajo acoplamiento, alta cohesión. stdlib > dependencias externas.

## Por lenguaje/framework
- **Python**: type hints, PEP 8, async, funciones pequeñas.
- **Angular**: Standalone Components, Signals, sin NgModules salvo necesario.
- **Flutter**: Material 3, widgets pequeños, optimiza rebuilds.

## Rendimiento y seguridad
Validación inputs, protección credenciales, prevención inyecciones, mínimo privilegio. No optimices prematuramente.

## Git
Múltiples archivos: resume cambios, archivos modificados, riesgos, mensaje descriptivo.

## Actitud
Compañero técnico, no complaciente. Señala malas prácticas con argumentos.

## Archivos grandes
Para archivos extensos (>500 líneas o con contenido complejo), escribir en chunks o usar scripts generadores en lugar de intentar escribir todo el contenido en una sola operación. Usar `write` para crear archivos pequeños y `edit` para extender, o crear scripts Python/Node que generen el contenido final.

## Context7 MCP
Usa `context7_resolve-library-id` y `context7_query-docs` automáticamente para cualquier librería/framework.

## Playwright MCP

### Problema conocido
`playwright-cli` no está instalado globalmente. Usar siempre `npx playwright cli` en lugar del comando directo.

### Variables de entorno obligatorias
Siempre establecer estas vars antes de ejecutar cualquier comando Playwright:

```bash
export PLAYWRIGHT_MCP_EXECUTABLE_PATH=/usr/bin/chromium
export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium
export BROWSER=chromium
```

Sin estas vars, Playwright intenta usar "chrome-for-testing" (su Chromium descargado) y falla con: `Browser "chrome-for-testing" is not installed`.

### Sintaxis correcta
```bash
# Abrir navegador headless
PLAYWRIGHT_MCP_EXECUTABLE_PATH=/usr/bin/chromium PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium BROWSER=chromium npx playwright cli open --browser=chromium --no-headed

# Con URL
PLAYWRIGHT_MCP_EXECUTABLE_PATH=/usr/bin/chromium PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium BROWSER=chromium npx playwright cli open https://example.com --browser=chromium --no-headed

# En comandos posteriores la sesión se mantiene, solo agregar las vars si es una nueva shell
PLAYWRIGHT_MCP_EXECUTABLE_PATH=/usr/bin/chromium PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium BROWSER=chromium npx playwright cli snapshot
PLAYWRIGHT_MCP_EXECUTABLE_PATH=/usr/bin/chromium PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium BROWSER=chromium npx playwright cli close
```

### Servidor MCP (`@playwright/mcp`)
El servidor MCP usado por opencode ya tiene las vars configuradas en `opencode.jsonc`. Si el servidor falla al arrancar, verificar:
- `/usr/bin/chromium` existe y es ejecutable
- No hay procesos `chrome`/zombies colgando: `pkill -f chromium` antes de reiniciar
- Versión: `npx playwright --version` (actual: 1.62.1)
