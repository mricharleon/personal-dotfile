python3 -c "
import subprocess, psutil, re

# 1. Obtener la memoria usada realmente por el OS vía vm_stat
vm_output = subprocess.check_output('vm_stat', text=True)
pages = {}
for line in vm_output.splitlines()[1:]:
    parts = line.split(':')
    if len(parts) == 2:
        key = parts[0].strip()
        val = int(re.sub(r'[^\d]', '', parts[1]))
        pages[key] = val

page_size = 4096 # 4KB por página en Apple Silicon
wired = (pages.get('Pages wired down', 0) * page_size) / (1024**3)
active = (pages.get('Pages active', 0) * page_size) / (1024**3)
compressed = (pages.get('Pages occupied by compressor', 0) * page_size) / (1024**3)

# En macOS, el OS 'puro' (Wired + Compressed) es lo que el Kernel no puede mandar a disco
os_base_gb = wired + compressed

# Memoria total usada según el Kernel
vm = psutil.virtual_memory()
total_used_gb = vm.used / (1024**3)
total_ram_gb = vm.total / (1024**3)
swap_gb = psutil.swap_memory().used / (1024**3)

# La diferencia entre el uso total y el OS base es lo que consumen tus procesos de IA
ia_real_gb = max(0.0, total_used_gb - os_base_gb)

print('--- DESGLOSE NATIVO REAL (MACOS) ---')
print(f'macOS Kernel/OS Base : {os_base_gb:.2f} GB  (Wired + Memoria Comprimida)')
print(f'omlx Server (IA Total): {ia_real_gb:.2f} GB  (Modelo + KV Cache + CPU)')
print(f'------------------------------------')
print(f'RAM Usada Total      : {total_used_gb:.2f} GB / {total_ram_gb:.2f} GB')
print(f'RAM Libre Real       : {(total_ram_gb - total_used_gb):.2f} GB')
print(f'Swap Activo          : {swap_gb:.2f} GB')
"

