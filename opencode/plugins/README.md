# Plugins

## omlx-top-p-stripper.py — Proxy para corrección de top_p

### Qué hace

Intercepta las peticiones que opencode envía a OMLX y remueve el campo `top_p` del JSON antes de reenviarlas. Esto permite que OMLX use su propio valor configurado (`top_p: 0.92`) en lugar del default de 1.0 que envía el SDK de opencode por defecto.

### Arquitectura

```
opencode → localhost:8081 (proxy) → 192.168.2.138:8080 (OMLX)
```

El proxy corre como servicio systemd (`omlx-proxy.service`), escuchando en `127.0.0.1:8081`.

### Por qué existe

El SDK `@ai-sdk/openai-compatible` que usa opencode siempre envía `top_p=1.0` en las peticiones, ignorando cualquier valor configurado en `agent.build.options.topP` o `provider.models.*.options.topP`. OMLX prioriza el valor del cliente sobre su propia configuración.

Sin este proxy, ambos agentes (build y plan) usarían `top_p=1.0`, anulando el ajuste de `0.92` que se configuró en OMLX para mejorar la precisión del modelo cuantizado a 4-bit.

### Configuración actual

| Parámetro | Valor | Razón |
|-----------|-------|-------|
| `temperature` (build) | 0.45 | Compensa ruido de cuantización 4-bit |
| `temperature` (plan) | 0.25 | Planificación requiere más determinismo |
| `top_k` (build) | 50 | Más opciones dentro del rango conservador |
| `top_k` (plan) | 20 | Igual que recomendación oficial de Qwen3 |
| `repetition_penalty` (build) | 1.08 | Penaliza repeticiones, artefacto común de 4-bit |
| `repetition_penalty` (plan) | 1.05 | Penalización más suave para planificación |
| `top_p` (OMLX) | 0.92 | Proxy remueve el enviado por opencode (1.0) |

### Archivos

- `omlx-top-p-stripper.py` — Script del proxy (Python, stdlib)
- `omlx-proxy.service` — Unit file de systemd para persistencia

### Estado del servicio

```bash
# Ver estado
systemctl status omlx-proxy

# Iniciar/detener/reiniciar
sudo systemctl start|stop|restart omlx-proxy

# Verificar que escucha en localhost:8081
ss -tlnp | grep 8081

# Logs del proxy
journalctl -u omlx-proxy --follow
```

### Debug

Si el proxy deja de funcionar:

1. Verificar que esté activo: `systemctl status omlx-proxy`
2. Verificar puerto: `ss -tlnp | grep 8081`
3. Verificar logs: `journalctl -u omlx-proxy -n 50`
4. Reiniciar: `sudo systemctl restart omlx-proxy`

Si opencode no puede conectar al proxy, verificar que `baseURL` en `opencode.jsonc` apunte a `http://127.0.0.1:8081/v1`.
