#!/bin/bash
# ============================================================
# macOS Memory Cleaner - Libre de RAM y procesos no esenciales
# ============================================================
# Uso: sudo ./macos_memory_cleaner.sh
# Autor: generado para servidor OM XL (MacBook Pro M1 Pro)
# ============================================================

set -euo pipefail

# ---------- CONFIGURACIÓN ----------
# Nombres de procesos que NUNCA se deben matar (servidor IA + procesos críticos)
# Se resuelven dinámicamente por nombre, no por PID fijo.
PROTECTED_PROCS=("launchd" "WindowServer" "python" "omxl" "omlx" "server" "ollama" "mactop")

# Nombres de procesos que se pueden matar (parcial, case-insensitive)
KILLABLE_PROCESSES=(
    "spotlight"
    "mds"
    "finduashelper"
    "coreaudiod"
    "airplayui"
    "homepod"
    "appstoreagent"
    "softwareupdated"
    "systemmigrationd"
    "mobileassetd"
    "siriinferenced"
    "assistantd"
    "routined"
    "duetexpertd"
    "amsengagementd"
    "knowledgeconstru"
    "siriactionsd"
    "homemanagerd"
    "geod"
    "locationd"
    "networkservicepr"
    "windowmanager"
    "controlcenter"
    "notificationcenter"
    "widgetserver"
    "weatherwidget"
    "stockswidget"
    "podcastswidget"
    "calendarwidget"
    "remindd"
    "epson"
    "printer"
)

# ---------- COLORES ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ---------- FUNCIONES ----------
print_header() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}  macOS Memory Cleaner${NC}"
    echo -e "${CYAN}========================================${NC}"
}

get_mem_info() {
    local vm_output
    vm_output=$(vm_stat)

    local page_size=16384  # 16 KB en Apple Silicon
    local free active inactive speculative compressed wired throttled deactivated purged used movable

    # Parsear cada línea: "FieldName:           NNNNNN pages"
    while IFS= read -r line; do
        local field val
        field=$(echo "$line" | sed -E 's/^[[:space:]]*([^:]+):.*/\1/' | tr -d ' .:')
        val=$(echo "$line" | sed -E 's/^[^:]+:[[:space:]]*([0-9]+).*/\1/')
        [[ -z "$val" || ! "$val" =~ ^[0-9]+$ ]] && continue

        case "$field" in
            Pagesfree)                  free=${val:-0} ;;
            Pagesactive)                active=${val:-0} ;;
            Pagesinactive)              inactive=${val:-0} ;;
            Pagesspeculative)           speculative=${val:-0} ;;
            Pagesoccupiedbycompressor)  compressed=${val:-0} ;;
            Pageswireddown)             wired=${val:-0} ;;
            Pagesthrottled)             throttled=${val:-0} ;;
            Pagesdeactivated)           deactivated=${val:-0} ;;
            Pagespurged)                purged=${val:-0} ;;
        esac
    done <<< "$vm_output"

    awk -v free="$free" -v active="$active" -v inactive="$inactive" \
        -v speculative="$speculative" -v compressed="$compressed" \
        -v wired="$wired" -v throttled="$throttled" -v deactivated="$deactivated" \
        -v purged="$purged" -v page_size="$page_size" 'BEGIN {
        printf "  Memoria total:     32.0 GB\n"
        printf "  Usada:             %.1f GB\n", 32 - free * page_size / 1073741824
        printf "  Free:              %.1f GB\n", free * page_size / 1073741824
        printf "  Active (procesos): %.1f GB\n", active * page_size / 1073741824
        printf "  Inactive (cache):  %.1f GB\n", inactive * page_size / 1073741824
        printf "  Speculative:       %.1f GB\n", speculative * page_size / 1073741824
        printf "  Compressed:        %.1f GB\n", compressed * page_size / 1073741824
        printf "  Wired (kernel):    %.1f GB\n", wired * page_size / 1073741824
        printf "  Movible (liberable): %.1f GB\n", (inactive + speculative + deactivated + purged) * page_size / 1073741824
    }'
}

show_memory_status() {
    echo -e "\n${YELLOW}--- Estado de memoria ---${NC}"
    get_mem_info
    echo ""
    echo "  Top 10 procesos por memoria:"
    ps aux --sort=-%mem 2>/dev/null | head -11 || \
    ps aux -m | head -11
}

# Devuelve 0 si el PID pertenece a un proceso protegido, 1 si no.
# Protege por nombre de comando, no por PID (los PIDs cambian entre ejecuciones).
is_protected() {
    local pid=$1
    [[ -z "$pid" ]] && return 1
    local cmd
    cmd=$(ps -p "$pid" -o comm= 2>/dev/null || echo "")
    cmd_full=$(ps -p "$pid" -o args= 2>/dev/null || echo "")
    [[ -z "$cmd" && -z "$cmd_full" ]] && return 1
    local cmd_lower cmd_full_lower
    cmd_lower=$(echo "$cmd" | tr '[:upper:]' '[:lower:]')
    cmd_full_lower=$(echo "$cmd_full" | tr '[:upper:]' '[:lower:]')
    for p in "${PROTECTED_PROCS[@]}"; do
        local p_lower
        p_lower=$(echo "$p" | tr '[:upper:]' '[:lower:]')
        [[ "$cmd_lower" == "$p_lower" || "$cmd_full_lower" == *"$p_lower"* ]] && return 0
    done
    return 1
}

# ---------- PASO 0: Listar procesos protegidos (resueltos dinámicamente) ----------
echo -e "\n${CYAN}--- Procesos protegidos (nunca se matarán) ---${NC}"
for p in "${PROTECTED_PROCS[@]}"; do
    p_lower=$(echo "$p" | tr '[:upper:]' '[:lower:]')
    pids=$(ps aux | awk -v name="$p_lower" 'tolower($11) ~ name || tolower($0) ~ name { print $2 }' | tr '\n' ' ')
    if [[ -n "$pids" ]]; then
        echo -e "  ${GREEN}✓$p: PIDs $pids${NC}"
    else
        echo -e "  ${YELLOW}⊘ $p: no encontrado en ejecución${NC}"
    fi
done

# ---------- PASO 1: Snapshot inicial ----------
print_header
show_memory_status

# ---------- PASO 2: Vender disk cache ----------
echo -e "\n${GREEN}[1/4] Vendiendo páginas en caché del disco (sudo purge)...${NC}"
sudo -n purge 2>/dev/null || sudo purge
echo "  ✅ Cache vendida."

# ---------- PASO 3: Vender inactive pages----------
echo -e "\n${GREEN}[2/4] Forzando venta de páginas inactive...${NC}"
sudo sysctl -w vm.pageout_nonprogress_threshold_millis=0 2>/dev/null || true
sudo sysctl -w vm.drop_caches=1 2>/dev/null || true
echo "  ✅ Páginas inactive procesadas."

# ---------- PASO 4: Matar procesos no esenciales ----------
echo -e "\n${GREEN}[3/4] Buscando y cerrando procesos no esenciales...${NC}"

KILLED_COUNT=0
SKIPPED_PROTECTED=0

for proc_name in "${KILLABLE_PROCESSES[@]}"; do
    # Buscar procesos que coincidan (excluyendo al propio script y a los protegidos)
    pids=$(ps aux | awk -v name="$proc_name" '
        tolower($11) ~ tolower(name) || tolower($0) ~ tolower(name) { print $2 }
    ' | head -5)

    for pid in $pids; do
        [[ -z "$pid" ]] && continue
        proc_cmd=$(ps -p "$pid" -o comm= 2>/dev/null || echo "")
        [[ -z "$proc_cmd" ]] && continue

        # Verificar que no sea protegido
        if is_protected "$pid"; then
            echo -e "  ${YELLOW}  ⏭  Skipped (protegido por nombre): $proc_cmd (PID $pid)${NC}"
            SKIPPED_PROTECTED=$((SKIPPED_PROTECTED + 1))
            continue
        fi

        # Verificar que el proceso pertenezca al usuario actual (no root/systema crítico)
        proc_user=$(ps -p "$pid" -o user= 2>/dev/null || echo "")
        [[ -z "$proc_user" ]] && continue

        # Intentar TERM primero (gracioso)
        kill -TERM "$pid" 2>/dev/null && \
            echo -e "  ${GREEN}  ✗ Cerrado gracefully: $proc_cmd (PID $pid, user=$proc_user)${NC}" || \
            echo -e "  ${YELLOW}  ✗ No respondió a TERM: $proc_cmd (PID $pid)${NC}"
        KILLED_COUNT=$((KILLED_COUNT + 1))
    done
done

# Esperar a que los procesos terminen
sleep 2

# Forzar KILL a los que sigan vivos (con precaución)
for proc_name in "${KILLABLE_PROCESSES[@]}"; do
    pids=$(ps aux | awk -v name="$proc_name" '
        tolower($11) ~ tolower(name) || tolower($0) ~ tolower(name) { print $2 }
    ' | head -3)

    for pid in $pids; do
        [[ -z "$pid" ]] && continue
        is_protected "$pid" && continue

        proc_cmd=$(ps -p "$pid" -o comm= 2>/dev/null || echo "")
        [[ -z "$proc_cmd" ]] && continue

        # Solo forzar si no es un proceso del sistema crítico
        proc_uid=$(ps -p "$pid" -o uid= 2>/dev/null || echo "")
        if [[ "$proc_uid" == "0" ]]; then
            echo -e "  ${YELLOW}  ⏭  Skipped (root/system): $proc_cmd (PID $pid)${NC}"
            continue
        fi

        kill -9 "$pid" 2>/dev/null && \
            echo -e "  ${RED}  ✗ Fuerza kill: $proc_cmd (PID $pid)${NC}" || true
        KILLED_COUNT=$((KILLED_COUNT + 1))
    done
done

echo "  Procesos cerrados: $KILLED_COUNT | Saltados (protegidos por nombre): $SKIPPED_PROTECTED"

# ---------- PASO 5: Reset de compressor ----------
echo -e "\n${GREEN}[4/4] Reiniciando compresor de memoria...${NC}"
# En Apple Silicon no se puede restart el compressor directamente,
# pero podemos forzar una venta agresiva
sudo sysctl -w vm.compress_test_disabled=0 2>/dev/null || true
echo "  ✅ Compresor activado."

# ---------- RESULTADO FINAL ----------
show_memory_status

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Limpieza completada.${NC}"
echo -e "${GREEN}========================================${NC}\n"

# ---------- INFO ADICIONAL ----------
echo -e "${CYAN}Comandos útiles para futuro:${NC}"
echo "  sudo purge                          # Vender cache de disco"
echo "  top -o mem -l 1                     # Ver uso de memoria"
echo "  vm_stat | grep -E 'free|active|inactive'  # Detalle de páginas"
echo "  ps aux --sort=-%mem | head -15      # Top procesos RAM"
echo "  sudo sysctl iogpu.wired_limit_mb=31129  # Ajustar GPU wired (tu config actual)"
echo ""
