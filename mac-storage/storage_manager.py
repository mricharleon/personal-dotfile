#!/usr/bin/env python3
"""
mac-storage: Advanced macOS Storage Manager for Developers
Interactive TUI to analyze and clean up disk space.

REQUIRES: macOS + Python 3.10+
INSTALL: pip install -r requirements.txt
RUN:     python storage_manager.py
"""

import os
import sys
import subprocess
import shutil
import time
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

try:
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.columns import Columns
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich.layout import Layout
    from rich.tree import Tree
    from rich import box
    from rich.align import Align
    from rich.rule import Rule
    import readchar
except ImportError:
    print("ERROR: rich and readchar required. Install with: pip install -r requirements.txt")
    sys.exit(1)

console = Console()


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class StorageItem:
    path: str
    size: int
    category: str
    description: str
    safe_to_delete: bool = True
    files_count: int = 0
    age_days: Optional[int] = None
    cleanup_action: str = ""
    cleanup_warning: str = ""

    @property
    def size_human(self) -> str:
        return format_bytes(self.size)

    @property
    def selected(self) -> bool:
        return getattr(self, '_selected', False)

    def toggle(self):
        self._selected = not getattr(self, '_selected', False)


@dataclass
class ScanResult:
    total_size: int = 0
    items: list = field(default_factory=list)

    def add(self, item: StorageItem):
        self.items.append(item)
        self.total_size += item.size

    def sort_by_size(self, reverse: bool = True):
        self.items.sort(key=lambda x: x.size, reverse=reverse)

    def selected_size(self) -> int:
        return sum(i.size for i in self.items if i.selected)


# ============================================================================
# UTILITIES
# ============================================================================

def format_bytes(b: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def run_cmd(cmd: list, capture: bool = True) -> tuple:
    try:
        r = subprocess.run(cmd, capture_output=capture, text=True, timeout=30)
        return r.returncode == 0, (r.stdout if capture else "")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""


def get_disk_usage() -> dict:
    ok, out = run_cmd(["df", "-h", "/"])
    if not ok:
        return {}
    lines = out.strip().split("\n")
    if len(lines) < 2:
        return {}
    parts = lines[-1].split()
    return {
        "total": parts[1] if len(parts) > 1 else "?",
        "used": parts[2] if len(parts) > 2 else "?",
        "available": parts[3] if len(parts) > 3 else "?",
        "percent": parts[4] if len(parts) > 4 else "?",
    }


def dir_size_fast(path: str) -> int:
    ok, out = run_cmd(["du", "-sk", path])
    if ok:
        try:
            return int(out.split()[0]) * 1024
        except (ValueError, IndexError):
            pass
    try:
        return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file())
    except (PermissionError, OSError):
        return 0


def file_age_days(path: str) -> Optional[int]:
    try:
        mtime = os.path.getmtime(path)
        return (time.time() - mtime) / 86400
    except OSError:
        return None


def find_large_files(base: str, min_size: int = 500 * 1024 * 1024, limit: int = 50) -> list:
    items = []
    ok, out = run_cmd([
        "find", base, "-type", "f", "-size", "+500M",
        "-exec", "ls", "-d1", "-g", "-S", "{}", "+"
    ])
    if ok:
        for line in out.strip().split("\n")[:limit]:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            try:
                size = int(parts[0]) * 1024
                fpath = " ".join(parts[1:])
                items.append(StorageItem(
                    path=fpath, size=size, category="large_files",
                    description=f"Archivo grande ({format_bytes(size)})",
                    safe_to_delete=False,
                    age_days=int(file_age_days(fpath) or 0)
                ))
            except (ValueError, IndexError):
                continue
    return items[:limit]


def safe_delete(path: str) -> tuple:
    try:
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            if os.path.islink(path):
                os.unlink(path)
            else:
                os.remove(path)
        return True, None
    except Exception as e:
        return False, str(e)


# ============================================================================
# SCANNER
# ============================================================================

class Scanner:
    def __init__(self):
        self.home = Path.home()
        self.results: dict = {}

    def scan_all(self) -> dict:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Scanning disk usage...[/]"),
            console=console,
        ) as p:
            task = p.add_task("Scanning", total=None)
            self.results = {
                "xcode": self.scan_xcode(),
                "docker": self.scan_docker(),
                "homebrew": self.scan_homebrew(),
                "package_managers": self.scan_package_managers(),
                "dev_caches": self.scan_dev_caches(),
                "app_caches": self.scan_app_caches(),
                "large_files": self.scan_large_files(),
                "ios_simulators": self.scan_ios_simulators(),
                "logs_temp": self.scan_logs_temp(),
                "trash": self.scan_trash(),
                "system_temp": self.scan_system_temp(),
            }
            p.update(task, completed=1)
        return self.results

    def scan_xcode(self) -> ScanResult:
        r = ScanResult()
        cleanup_meta = {
            "DerivedData": {
                "action": "rm -rf ~/Library/Developer/Xcode/DerivedData/*",
                "warning": "Los artefactos de compilación se volverán a descargar en el próximo build. Seguro de eliminar.",
            },
            "Archives": {
                "action": "rm -rf ~/Library/Developer/Xcode/Archives/*.xcarchive",
                "warning": "Se eliminarán los bundles archivados para App Store/TestFlight. Conservar si se necesitan enviar actualizaciones.",
            },
            "DeviceLogs": {
                "action": "rm -rf ~/Library/Logs/DiagnosticReports/*",
                "warning": "Los logs de diagnóstico y crash se regenerarán.",
            },
            "Profiles": {
                "action": "",
                "warning": "Los profiles de aprovisionamiento son necesarios para firmar y desplegar apps. No eliminar.",
            },
        }
        dirs = {
            "DerivedData": str(self.home / "Library/Developer/Xcode/DerivedData"),
            "Archives": str(self.home / "Library/Developer/Xcode/Archives"),
            "DeviceLogs": str(self.home / "Library/Logs/CoreSimulator"),
            "Profiles": str(self.home / "Library/MobileDevice/Provisioning Profiles"),
        }
        for name, path in dirs.items():
            if os.path.isdir(path):
                size = dir_size_fast(path)
                if size > 10 * 1024 * 1024:
                    meta = cleanup_meta.get(name, {})
                    r.add(StorageItem(
                        path=path, size=size, category="xcode",
                        description=f"Xcode {name}",
                        safe_to_delete=name != "Profiles",
                        cleanup_action=meta.get("action", ""),
                        cleanup_warning=meta.get("warning", ""),
                    ))
        return r

    def scan_ios_simulators(self) -> ScanResult:
        r = ScanResult()
        ok, out = run_cmd(["xcrun", "simctl", "list", "devices", "json"])
        if ok:
            try:
                data = json.loads(out)
                for dev_list in data.get("devices", {}).values():
                    for d in dev_list:
                        if d.get("isAvailable") is False:
                            path = d.get("path", "")
                            if path:
                                size = dir_size_fast(path)
                                if size > 50 * 1024 * 1024:
                                    r.add(StorageItem(
                                        path=path, size=size,
                                        category="ios_simulators",
                                        description=f"Simulador: {d.get('name', 'Desconocido')}",
                                        safe_to_delete=True,
                                        cleanup_action=f"xcrun simctl delete {d.get('udid', '')}",
                                        cleanup_warning="Los simuladores eliminados y sus datos se perderán. Reagregar desde Xcode.",
                                    ))
            except (json.JSONDecodeError, KeyError):
                pass
        sim_path = str(self.home / "Library/Developer/CoreSimulator")
        if os.path.isdir(sim_path):
            size = dir_size_fast(sim_path)
            if size > 50 * 1024 * 1024:
                r.add(StorageItem(
                    path=sim_path, size=size,
                    category="ios_simulators",
                    description="Datos CoreSimulator",
                    safe_to_delete=True,
                    cleanup_action="rm -rf ~/Library/Developer/CoreSimulator/*",
                    cleanup_warning="Se perderán todos los datos de runtime de simuladores. Re-descargar desde Xcode.",
                ))
        return r

    def scan_docker(self) -> ScanResult:
        r = ScanResult()
        action_map = {
            "Images": ("docker image prune -a --force", "Todas las imágenes sin usar serán eliminadas. Los contenedores en ejecución dependen de sus imágenes."),
            "Containers": ("docker container prune --force", "Todos los contenedores detenidos serán eliminados. Los datos en volumes se preservan."),
            "Local Volumes": ("docker volume prune --force", "Todos los volumes sin usar serán eliminados. Los datos se perderán."),
            "Build Cache": ("docker builder prune --force", "El cache de compilación será borrado. Las compilaciones futuras pueden tardar más."),
            "tmpfs": ("docker system prune --volumes --force", "tmpfs y datos colgantes serán eliminados."),
            "Proxy Cache": ("docker system prune --all --force", "Los datos cache del registro se volverán a obtener en el próximo pull."),
        }
        ok, out = run_cmd(["docker", "system", "df", "-v"])
        if ok:
            try:
                data = json.loads(out)
                desc_map = {
                    "Images": "Imágenes Docker",
                    "Containers": "Contenedores Docker",
                    "Local Volumes": "Volumes Docker",
                    "Build Cache": "Cache de compilación Docker",
                    "tmpfs": "tmpfs Docker",
                    "Proxy Cache": "Cache proxy Docker",
                }
                for k, v in data.items():
                    if isinstance(v, dict) and "TotalSize" in v:
                        size = v.get("TotalSize", 0) or 0
                        if size > 10 * 1024 * 1024:
                            meta = action_map.get(k, ("", ""))
                            r.add(StorageItem(
                                path="docker://", size=size,
                                category="docker",
                                description=desc_map.get(k, f"Docker {k}"),
                                safe_to_delete=True,
                                cleanup_action=meta[0],
                                cleanup_warning=meta[1],
                            ))
            except (json.JSONDecodeError, KeyError):
                pass
        docker_dir = str(self.home / "Library/docker")
        if os.path.isdir(docker_dir):
            size = dir_size_fast(docker_dir)
            if size > 50 * 1024 * 1024:
                r.add(StorageItem(
                    path=docker_dir, size=size,
                    category="docker",
                    description="Archivos locales Docker",
                    safe_to_delete=True,
                    cleanup_action="docker system prune -a --volumes --force",
                    cleanup_warning="Elimina TODOS los datos Docker sin usar: imágenes, contenedores, volumes, redes. Peligroso.",
                ))
        return r

    def scan_homebrew(self) -> ScanResult:
        r = ScanResult()
        cleanup_meta = {
            "Caches": {
                "action": "brew cleanup --prune=all && rm -rf ~/Library/Caches/Homebrew",
                "warning": "Se eliminarán descargas cacheadas y versiones antiguas de fórmulas. Necesarias nuevas descargas para reinstalar.",
            },
            "Cask Casks": {
                "action": "rm -rf ~/Library/Caches/Homebrew/Cask/*",
                "warning": "Se eliminarán caches de instaladores de Cask. Seguro de eliminar.",
            },
            "Cask": {
                "action": "rm -rf ~/Library/Caches/Homebrew/Cask/*",
                "warning": "Se eliminarán caches de instaladores de Cask. Seguro de eliminar.",
            },
            "Linked": {
                "action": "",
                "warning": "Los kegs enlazados son enlaces simbólicos a paquetes instalados. No eliminar.",
            },
        }
        dirs = {
            "Caches": str(self.home / "Library/Caches/Homebrew"),
            "Cask Caches": str(self.home / "Library/Caches/Homebrew/Cask"),
            "Linked": str(self.home / "Library/LinkedKegs"),
        }
        for name, path in dirs.items():
            if os.path.isdir(path):
                size = dir_size_fast(path)
                if size > 10 * 1024 * 1024:
                    meta = cleanup_meta.get(name, {})
                    r.add(StorageItem(
                        path=path, size=size, category="homebrew",
                        description=f"Homebrew {name}",
                        safe_to_delete=name != "Linked",
                        cleanup_action=meta.get("action", ""),
                        cleanup_warning=meta.get("warning", ""),
                    ))
        return r

    def scan_package_managers(self) -> ScanResult:
        r = ScanResult()
        cleanup_meta = {
            "npm cache": {
                "action": "npm cache clean --force",
                "warning": "El cache de npm se repoblará en el próximo install.",
            },
            "yarn cache": {
                "action": "yarn cache clean",
                "warning": "El cache de Yarn se repoblará en el próximo install.",
            },
            "pip cache": {
                "action": "pip cache purge",
                "warning": "Se eliminarán los archives wheel descargados. Se volverán a descargar en el próximo pip install.",
            },
            "pipx cache": {
                "action": "rm -rf ~/Library/Caches/pipx/*",
                "warning": "Seguro de eliminar. pipx volverá a descargar en el próximo install.",
            },
            "cargo registry": {
                "action": "rm -rf ~/.cargo/registry/cache/* && rm -rf ~/.cargo/registry/src/*",
                "warning": "Los crates descargados se volverán a obtener en el próximo cargo build/install.",
            },
            "cargo git": {
                "action": "rm -rf ~/.cargo/git/db/*",
                "warning": "Se eliminarán los caches de git clone para dependencias. Se reclonarán en el próximo build.",
            },
            "go build cache": {
                "action": "go clean -cache",
                "warning": "Cache de compilación de Go borrado. La primera recompilación después de la limpieza será más lenta.",
            },
            "go mod cache": {
                "action": "go clean -modcache",
                "warning": "Cache de descargas de módulos Go borrado. Se volverá a descargar en el próximo build.",
            },
            "sbt cache": {
                "action": "rm -rf ~/Library/Caches/sbt/*",
                "warning": "Cache Ivy de sbt borrado. Se volverá a descargar en el próximo build.",
            },
            "gradle cache": {
                "action": "rm -rf ~/.gradle/caches/*",
                "warning": "Cache de compilación de Gradle borrado. La primera compilación será más lenta.",
            },
            "maven cache": {
                "action": "mvn dependency:purge-local-repository",
                "warning": "Los artefactos del repositorio Maven local se volverán a obtener.",
            },
            "CocoaPods": {
                "action": "rm -rf ~/Library/Caches/CocoaPods/*",
                "warning": "Cache de descargas de CocoaPods borrado. Seguro de eliminar.",
            },
            "pub cache": {
                "action": "pub cache clean",
                "warning": "Cache de Dart pub borrado. Se volverá a descargar en el próximo pub get.",
            },
            "deno cache": {
                "action": "deno cache --reload",
                "warning": "Cache remoto de Deno recargado. Los archivos de cache existentes son seguros de eliminar.",
            },
            "bun cache": {
                "action": "bun install --force",
                "warning": "Cache de instalación de Bun borrado.",
            },
            "pnpm": {
                "action": "pnpm store prune",
                "warning": "Tienda pnpm podada. Paquetes sin usar eliminados del store.",
            },
        }
        dirs = {
            "npm cache": str(self.home / "Library/Caches/npm"),
            "yarn cache": str(self.home / "Library/Caches/yarn"),
            "pip cache": str(self.home / "Library/Caches/pip"),
            "pipx cache": str(self.home / "Library/Caches/pipx"),
            "cargo registry": str(self.home / ".cargo/registry"),
            "cargo git": str(self.home / ".cargo/git"),
            "go build cache": str(self.home / "Library/Caches/go-build"),
            "go mod cache": str(self.home / "Library/Caches/go-mod"),
            "sbt cache": str(self.home / "Library/Caches/sbt"),
            "gradle cache": str(self.home / ".gradle/caches"),
            "maven cache": str(self.home / ".m2/repository"),
            "CocoaPods": str(self.home / "Library/Caches/CocoaPods"),
            "pub cache": str(self.home / ".pub-cache"),
            "deno cache": str(self.home / "Library/Caches/deno"),
            "bun cache": str(self.home / "Library/Caches/bun"),
            "pnpm": str(self.home / "Library/Caches/pnpm"),
        }
        for name, path in dirs.items():
            if os.path.isdir(path):
                size = dir_size_fast(path)
                if size > 50 * 1024 * 1024:
                    meta = cleanup_meta.get(name, {})
                    r.add(StorageItem(
                        path=path, size=size, category="package_managers",
                        description=f"{name}",
                        safe_to_delete=True,
                        cleanup_action=meta.get("action", ""),
                        cleanup_warning=meta.get("warning", ""),
                    ))
        return r

    def scan_dev_caches(self) -> ScanResult:
        r = ScanResult()
        cleanup_meta = {
            "Flutter": {
                "action": "flutter clean && flutter pub cache repair",
                "warning": "Los artefactos de compilación de Flutter y el SDK descargado se volverán a obtener.",
            },
            "Android SDK": {
                "action": "",
                "warning": "El SDK de Android es necesario para compilar apps Android. No eliminar.",
            },
            "Android AVD": {
                "action": "rm -rf ~/Library/Android/sdk/avd/*",
                "warning": "Las imágenes y datos de emuladores Android se perderán. Recrear desde Android Studio.",
            },
            "JetBrains": {
                "action": "rm -rf ~/Library/Caches/JetBrains/*",
                "warning": "Se borrarán caches, índices y archivos temporales de IDEs. Seguro de eliminar. Los IDEs reconstruirán al iniciar.",
            },
            "VSCode extensions": {
                "action": "",
                "warning": "Las extensiones de VSCode son necesarias. Eliminar desde la interfaz de VSCode.",
            },
            "dart cache": {
                "action": "rm -rf ~/.dart_server/*",
                "warning": "Cache del servidor de análisis Dart borrado. Seguro de eliminar.",
            },
        }
        dirs = {
            "Flutter": str(self.home / "Library/Caches/flutter"),
            "Android SDK": str(self.home / "Library/Android/sdk"),
            "Android AVD": str(self.home / "Library/Android/sdk/avd"),
            "JetBrains": str(self.home / "Library/Caches/JetBrains"),
            "VSCode extensions": str(self.home / ".vscode/extensions"),
            "dart cache": str(self.home / ".dart_server"),
        }
        for name, path in dirs.items():
            if os.path.isdir(path):
                size = dir_size_fast(path)
                if size > 100 * 1024 * 1024:
                    meta = cleanup_meta.get(name, {})
                    r.add(StorageItem(
                        path=path, size=size, category="dev_caches",
                        description=f"Dev: {name}",
                        safe_to_delete=name not in ("Android SDK", "Android AVD"),
                        cleanup_action=meta.get("action", ""),
                        cleanup_warning=meta.get("warning", ""),
                    ))
        return r

    def scan_app_caches(self) -> ScanResult:
        r = ScanResult()
        cache_dir = self.home / "Library/Caches"
        if os.path.isdir(cache_dir):
            sizes = []
            for d in cache_dir.iterdir():
                if d.is_dir():
                    size = dir_size_fast(str(d))
                    if size > 100 * 1024 * 1024:
                        sizes.append((d.name, size, d))
            sizes.sort(key=lambda x: x[1], reverse=True)
            for name, size, d in sizes[:20]:
                r.add(StorageItem(
                    path=str(d), size=size, category="app_caches",
                    description=f"cache de {name}",
                    safe_to_delete=True,
                    cleanup_action=f"rm -rf \"{d}\"",
                    cleanup_warning=f"Cache de la aplicación {name}. Se regenerará. Puede ser necesario volver a iniciar sesión.",
                ))
        return r

    def scan_large_files(self) -> ScanResult:
        r = ScanResult()
        skip_prefixes = [
            str(self.home / "Library/Developer"),
            str(self.home / "Library/Caches"),
            str(self.home / "Library/Application Support"),
        ]
        items = find_large_files(str(self.home), min_size=500 * 1024 * 1024, limit=30)
        for item in items:
            if not any(item.path.startswith(p) for p in skip_prefixes):
                r.add(item)
        r.sort_by_size()
        return r

    def scan_logs_temp(self) -> ScanResult:
        r = ScanResult()
        cleanup_meta = {
            "System Logs": {
                "action": "rm -rf ~/Library/Logs/*",
                "warning": "Los logs de aplicaciones se regenerarán. Seguro de eliminar.",
            },
            "Crash Reports": {
                "action": "rm -rf ~/Library/Logs/DiagnosticReports/*",
                "warning": "Reports de crash y datos de diagnóstico borrados. Útil si el troubleshooting está completo.",
            },
            "Temp files": {
                "action": "rm -rf /tmp/* && rm -rf ~/tmp/*",
                "warning": "Se eliminarán todos los archivos temporales. Las apps en ejecución pueden verse afectadas.",
            },
        }
        dirs = {
            "System Logs": str(self.home / "Library/Logs"),
            "Crash Reports": str(self.home / "Library/Logs/DiagnosticReports"),
            "Temp files": "/tmp",
        }
        for name, path in dirs.items():
            if os.path.isdir(path):
                size = dir_size_fast(path)
                if size > 50 * 1024 * 1024:
                    meta = cleanup_meta.get(name, {})
                    r.add(StorageItem(
                        path=path, size=size, category="logs_temp",
                        description=name,
                        safe_to_delete=True,
                        cleanup_action=meta.get("action", ""),
                        cleanup_warning=meta.get("warning", ""),
                    ))
        return r

    def scan_trash(self) -> ScanResult:
        r = ScanResult()
        cleanup_meta = {
            "Trash": {
                "action": "rm -rf ~/.Trash/*",
                "warning": "Se eliminarán permanentemente todos los archivos en la Papelera. Esta acción no se puede deshacer.",
            },
            "Trash (user)": {
                "action": "rm -rf ~/.Trash/*",
                "warning": "Se eliminarán permanentemente todos los archivos en la Papelera. Esta acción no se puede deshacer.",
            },
        }
        trash_paths = {
            "Trash": str(self.home / ".Trash"),
        }
        for name, path in trash_paths.items():
            if os.path.isdir(path):
                size = dir_size_fast(path)
                if size > 10 * 1024 * 1024:
                    meta = cleanup_meta.get(name, {})
                    r.add(StorageItem(
                        path=path, size=size, category="trash",
                        description="Papelera del sistema",
                        safe_to_delete=True,
                        cleanup_action=meta.get("action", ""),
                        cleanup_warning=meta.get("warning", ""),
                    ))
        return r

    def scan_system_temp(self) -> ScanResult:
        r = ScanResult()
        cleanup_meta = {
            "/tmp": {
                "action": "rm -rf /tmp/*",
                "warning": "Se eliminarán todos los archivos temporales del sistema. Las apps en ejecución pueden verse afectadas.",
            },
            "/private/tmp": {
                "action": "rm -rf /private/tmp/*",
                "warning": "Se eliminarán todos los archivos temporales del sistema. Las apps en ejecución pueden verse afectadas.",
            },
            "~/tmp": {
                "action": "rm -rf ~/tmp/*",
                "warning": "Se eliminarán todos los archivos temporales del usuario. Las apps en ejecución pueden verse afectadas.",
            },
            "ASAuthorization": {
                "action": "rm -rf ~/Library/Caches/com.apple.AuthBrokerAgent/*",
                "warning": "Se eliminarán caches de autenticación. Puede ser necesario volver a iniciar sesión en aplicaciones.",
            },
            "Spotlight": {
                "action": "",
                "warning": "Los índices de Spotlight se regenerarán automáticamente. No eliminar manualmente.",
            },
            "CoreLocation": {
                "action": "rm -rf ~/Library/Caches/com.apple.LaunchServices-*.lstore2",
                "warning": "Se eliminarán caches de ubicación. Las apps de ubicación se regenerarán.",
            },
            "WiFi": {
                "action": "rm -rf ~/Library/Caches/com.apple.wifiwizard*/",
                "warning": "Se eliminarán caches de redes WiFi. Las redes guardadas persisten.",
            },
            "AddressBook": {
                "action": "rm -rf ~/Library/Caches/com.apple.AddressBook/*",
                "warning": "Se eliminarán caches de contactos. Se regenerarán al reiniciar Contactos.",
            },
            "Mail": {
                "action": "rm -rf ~/Library/Mail/V*/MailData/EDPushNotificationToken",
                "warning": "Se eliminarán caches de Mail. Los correos descargados se regenerarán.",
            },
            "QuickLook": {
                "action": "rm -rf ~/Library/Caches/com.apple.QuickLook/*",
                "warning": "Se eliminarán previews de Quick Look. Se regenerarán al previsualizar archivos.",
            },
            "Finder": {
                "action": "rm -rf ~/Library/Caches/com.apple.finder/*",
                "warning": "Se eliminarán caches de Finder. El Finder se reiniciará automáticamente.",
            },
            "iTunes": {
                "action": "rm -rf ~/Library/Caches/com.apple.iTunes/*",
                "warning": "Se eliminarán caches de iTunes. Se regenerarán al reiniciar iTunes.",
            },
            "Safari": {
                "action": "rm -rf ~/Library/Caches/com.apple.Safari/*",
                "warning": "Se eliminarán caches de Safari. Las páginas web se volverán a cargar.",
            },
            "Chrome": {
                "action": "rm -rf ~/Library/Caches/Google/Chrome/Default/*",
                "warning": "Se eliminarán caches de Chrome. Las páginas web se volverán a cargar.",
            },
            "Firefox": {
                "action": "rm -rf ~/Library/Caches/Mozilla/Firefox/*",
                "warning": "Se eliminarán caches de Firefox. Las páginas web se volverán a cargar.",
            },
        }
        dirs = {
            "/tmp": "/tmp",
            "/private/tmp": "/private/tmp",
            "~/tmp": str(self.home / "tmp"),
            "ASAuthorization": str(self.home / "Library/Caches/com.apple.AuthBrokerAgent"),
            "Spotlight": str(self.home / "Library/Caches/com.apple.Spotlight"),
            "CoreLocation": str(self.home / "Library/Caches/com.apple.CoreLocation"),
            "WiFi": str(self.home / "Library/Caches/com.apple.wifiwizard"),
            "AddressBook": str(self.home / "Library/Caches/com.apple.AddressBook"),
            "Mail": str(self.home / "Library/Mail/V*"),
            "QuickLook": str(self.home / "Library/Caches/com.apple.QuickLook"),
            "Finder": str(self.home / "Library/Caches/com.apple.finder"),
            "iTunes": str(self.home / "Library/Caches/com.apple.iTunes"),
            "Safari": str(self.home / "Library/Caches/com.apple.Safari"),
            "Chrome": str(self.home / "Library/Caches/Google/Chrome/Default"),
            "Firefox": str(self.home / "Library/Caches/Mozilla/Firefox"),
        }
        for name, path in dirs.items():
            if os.path.isdir(path):
                size = dir_size_fast(path)
                if size > 50 * 1024 * 1024:
                    meta = cleanup_meta.get(name, {})
                    r.add(StorageItem(
                        path=path, size=size, category="system_temp",
                        description=f"Temp: {name}",
                        safe_to_delete=True,
                        cleanup_action=meta.get("action", ""),
                        cleanup_warning=meta.get("warning", ""),
                    ))
        return r


# ============================================================================
# CATEGORY METADATA
# ============================================================================

CATEGORY_COLORS = {
    "xcode": "red",
    "docker": "blue",
    "homebrew": "yellow",
    "package_managers": "magenta",
    "dev_caches": "cyan",
    "app_caches": "green",
    "large_files": "white",
    "ios_simulators": "bright_magenta",
    "logs_temp": "grey62",
    "trash": "bright_red",
    "system_temp": "grey85",
}

CATEGORY_LABELS = {
    "xcode": "Xcode",
    "docker": "Docker",
    "homebrew": "Homebrew",
    "package_managers": "Gestores de Paquetes",
    "dev_caches": "Caches de Desarrollo",
    "app_caches": "Caches de Aplicaciones",
    "large_files": "Archivos Grandes (>500MB)",
    "ios_simulators": "Simuladores iOS",
    "logs_temp": "Logs y Temp",
    "trash": "Papelera",
    "system_temp": "Temporales del Sistema",
}

# Spanish UI strings
UI = {
    "title": "mac-storage",
    "subtitle": "Gestor Avanzado de Almacenamiento para Desarrolladores",
    "disk": "Disco",
    "used_of": "usado de",
    "available": "Disponible",
    "system": "Sistema",
    "storage_by_category": "Almacenamiento por Categoría",
    "category": "Categoría",
    "size": "Tamaño",
    "items": "Elementos",
    "share": "Porcentaje",
    "navigate_select": "↑↓ navegar | Enter seleccionar | teclas directas (x, do, ho, pm, dc, ac, lf, is, lt, tr, st) | D dashboard | Q salir",
    "category_hint": "↑↓ navegar | Enter abrir | teclas directas (x, do, ho, pm, dc, ac, lf, is, lt, tr, st) | D dashboard | Q salir",
    "dashboard_hint": "↑↓ navegar | Enter abrir | teclas directas (x, do, ho, pm, dc, ac, lf, is, lt, tr, st) | Q salir",
    "cleanup_hint": "↑↓ navegar | espacio seleccionar | a todos | A ninguno | p página- | n página+ | C = limpiar | B = volver | Q = salir",
    "goodbye": "¡Hasta luego!",
    "scanning": "Analizando uso de disco...",
    "cleaning": "Limpiando...",
    "cleanup_complete": "Limpieza Completa",
    "deleted": "Eliminados",
    "failed": "Fallidos",
    "freed": "Liberado",
    "before": "Antes",
    "after": "Después",
    "no_items_selected": "No hay elementos seleccionados para limpieza.",
    "permanently_delete": "Esto eliminará permanentemente los siguientes elementos.",
    "total_delete": "Total a eliminar:",
    "cleanup_details": "Detalles de Limpieza",
    "confirm_delete": "Escribe [bold red]SI[/] para confirmar la eliminación | cualquier otra tecla para cancelar",
    "no_categories": "No se encontraron categorías.",
    "no_data": "Sin datos para",
    "unknown_category": "Categoría desconocida",
    "selected": "Seleccionado",
    "page": "página",
    "and_more": "y más",
    "yes": "Sí",
    "no": "No",
    "dev": "Dev",
    "app_cache": "cache de",
    "and": "y",
}

CATEGORY_ORDER = [
    "xcode", "docker", "homebrew", "package_managers",
    "dev_caches", "app_caches", "large_files", "ios_simulators", "logs_temp",
    "trash", "system_temp",
]

# ============================================================================
# STORAGE MANAGER (TUI Controller)
# ============================================================================

class StorageManager:
    def __init__(self):
        self.scanner = Scanner()
        self.results: dict = {}
        self.current_category = None
        self.current_page = 0
        self.current_item = 0
        self.page_size = 15
        self.view_mode = "dashboard"  # dashboard | category | cleanup
        self.selected_items = []
        self.cat_list_index = 0

    def run(self):
        self._print_header()
        # Run initial scan
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Scanning disk usage...[/]"),
            console=console,
        ) as p:
            task = p.add_task("Scanning", total=None)
            self.results = self.scanner.scan_all()
            p.update(task, completed=1)

        self._show_dashboard()
        self._main_loop()

    def _read_key(self) -> str:
        try:
            return readchar.readkey()
        except (KeyboardInterrupt, EOFError):
            return "\x03"

    def _handle_dashboard_key(self, key: str):
        visible_cats = [c for c in CATEGORY_ORDER if c in self.results and self.results[c].total_size > 0]
        if key == "q":
            console.print(f"[dim]{UI['goodbye']}[/]")
            sys.exit(0)
        elif key == "\x03":
            console.print(f"\n[dim]{UI['goodbye']}[/]")
            sys.exit(0)
        elif key == "\n" or key == "\r":
            if visible_cats:
                cat = visible_cats[self.cat_list_index]
                self.view_mode = "category"
                self.current_category = cat
                self.current_page = 0
                self.current_item = 0
                console.clear()
                self._show_category(cat)
        elif key == "b" or key == "d":
            console.clear()
            self.view_mode = "dashboard"
            self.current_category = None
            self._show_dashboard()
        elif key == "\x1b[A":  # UP
            if visible_cats:
                self.cat_list_index = max(0, self.cat_list_index - 1)
                console.clear()
                self._show_dashboard()
        elif key == "\x1b[B":  # DOWN
            if visible_cats:
                self.cat_list_index = min(len(visible_cats) - 1, self.cat_list_index + 1)
                console.clear()
                self._show_dashboard()

    def _handle_category_key(self, key: str):
        sr = self.results.get(self.current_category)
        if not sr:
            return

        total_pages = (len(sr.items) + self.page_size - 1) // self.page_size

        # Arrow keys for navigation
        if key == "\x1b[A":  # UP
            if self.current_item < 0:
                self.current_item = 0
            self.current_item -= 1
            # Auto-page up
            if self.current_item < self.current_page * self.page_size:
                self.current_page = max(0, self.current_page - 1)
                self.current_item = min(0, self.current_page * self.page_size - 1)
            self._show_category(self.current_category)
            return
        elif key == "\x1b[B":  # DOWN
            self.current_item += 1
            max_item = len(sr.items) - 1
            if self.current_item > max_item:
                self.current_item = max_item
            # Auto-page down
            if self.current_item >= (self.current_page + 1) * self.page_size:
                self.current_page = min(total_pages - 1, self.current_page + 1)
            self._show_category(self.current_category)
            return

        # Space to toggle selected item
        if key == " ":
            items = sr.items
            if 0 <= self.current_item < len(items):
                items[self.current_item].toggle()
            self._show_category(self.current_category)
            return

        # Page navigation
        if key == "\x1b[C":  # RIGHT / n
            self.current_page = min(total_pages - 1, self.current_page + 1)
            self.current_item = self.current_page * self.page_size
            self._show_category(self.current_category)
            return
        if key == "\x1b[D":  # LEFT / p
            self.current_page = max(0, self.current_page - 1)
            self.current_item = self.current_page * self.page_size
            self._show_category(self.current_category)
            return

        # Regular key shortcuts
        if key == "c":  # Cleanup
            collected, total = self._show_cleanup_confirm()
            if collected:
                self._perform_cleanup(collected, total)
            self.view_mode = "dashboard"
            self.current_category = None
            self.current_item = 0
            self.current_page = 0
            console.clear()
            self._show_dashboard()
            return
        elif key == "b":  # Back
            self.view_mode = "dashboard"
            self.current_category = None
            self.current_item = 0
            self.current_page = 0
            console.clear()
            self._show_dashboard()
            return
        elif key == "d":  # Dashboard
            self.view_mode = "dashboard"
            self.current_category = None
            self.current_item = 0
            self.current_page = 0
            console.clear()
            self._show_dashboard()
            return
        elif key == "a":  # Select all
            for item in sr.items:
                item.toggle()
            self._show_category(self.current_category)
            return
        elif key == "A":  # Deselect all
            for item in sr.items:
                if item.selected:
                    item.toggle()
            self._show_category(self.current_category)
            return
        elif key == "q":
            console.print("[dim]Goodbye![/]")
            sys.exit(0)

    def _handle_category_list_key(self, key: str):
        if key == "q":
            console.print("[dim]Goodbye![/]")
            sys.exit(0)
        elif key == "\x03":
            console.print("\n[dim]Goodbye![/]")
            sys.exit(0)
        elif key == "b" or key == "d":
            console.clear()
            self.view_mode = "dashboard"
            self.current_category = None
            self._show_dashboard()
            return
        elif key == "\x1b[A":  # UP
            self.cat_list_index = max(0, self.cat_list_index - 1)
            self._show_category_list()
            return
        elif key == "\x1b[B":  # DOWN
            visible_cats = [c for c in CATEGORY_ORDER if c in self.results and self.results[c].total_size > 0]
            self.cat_list_index = min(len(visible_cats) - 1, self.cat_list_index + 1)
            self._show_category_list()
            return

        # Enter to select
        if key == "\n" or key == "\r":
            visible_cats = [c for c in CATEGORY_ORDER if c in self.results and self.results[c].total_size > 0]
            if 0 <= self.cat_list_index < len(visible_cats):
                cat = visible_cats[self.cat_list_index]
                self.view_mode = "category"
                self.current_category = cat
                self.current_page = 0
                self.current_item = 0
                self._show_category(cat)
            return

        # Direct category key mapping
        key_map = {
            "x": "xcode", "xd": "xcode", "xd": "xcode",
            "do": "docker",
            "ho": "homebrew",
            "pm": "package_managers", "package": "package_managers",
            "dc": "dev_caches", "dev": "dev_caches",
            "ac": "app_caches", "app": "app_caches",
            "lf": "large_files", "large": "large_files",
            "is": "ios_simulators", "sim": "ios_simulators",
            "lt": "logs_temp", "log": "logs_temp",
            "tr": "trash",
            "st": "system_temp",
        }

        # Try prefix matching first
        cat = None
        for c in CATEGORY_ORDER:
            if key == c or key == c[:3]:
                cat = c
                break

        if not cat:
            cat = key_map.get(key)

        if cat and cat in self.results and self.results[cat].total_size > 0:
            self.view_mode = "category"
            self.current_category = cat
            self.current_page = 0
            self.current_item = 0
            self._show_category(cat)
        else:
            console.print(f"[yellow]{UI['unknown_category']}: {key}[/]")
            time.sleep(0.5)
            self._show_category_list()

    def _print_header(self):
        console.print()
        console.print(Align.center(
            Text(UI["title"], style="bold cyan"),
        ))
        console.print(Align.center(
            Text(UI["subtitle"], style="dim"),
        ))
        console.print()

    # ---- DASHBOARD ----
    def _show_dashboard(self):
        disk = get_disk_usage()
        if not disk:
            console.print("[red]Could not read disk usage.[/]")
            return

        # Build category summary
        table = Table(title=UI["storage_by_category"], box=box.ROUNDED)
        table.add_column(UI["category"], style="cyan")
        table.add_column(UI["size"], justify="right", style="bold cyan")
        table.add_column(UI["items"], justify="right", style="dim")
        table.add_column(UI["share"], justify="center")

        grand_total = 0
        cat_sizes = []
        for cat in CATEGORY_ORDER:
            if cat in self.results:
                sr = self.results[cat]
                if sr.total_size > 0:
                    cat_sizes.append((cat, sr.total_size, len(sr.items)))
                    grand_total += sr.total_size

        cat_sizes.sort(key=lambda x: x[1], reverse=True)

        for i, (cat, size, count) in enumerate(cat_sizes):
            pct = (size / grand_total * 100) if grand_total > 0 else 0
            bar = "#" * int(pct / 2)
            color = CATEGORY_COLORS.get(cat, "white")
            is_selected = (i == self.cat_list_index)
            marker = " > " if is_selected else "   "
            cat_style = f"bold {color}" if is_selected else color
            table.add_row(
                f"[{cat_style}]{marker}{CATEGORY_LABELS.get(cat, cat)}[/]",
                f"[bold cyan]{format_bytes(size)}[/]",
                str(count),
                f"[{color}]{bar} {pct:.0f}%[/]",
            )

        # Disk usage bar
        used_pct = disk.get("percent", "?").replace("%", "")
        try:
            pct_val = int(used_pct)
        except ValueError:
            pct_val = 0

        if pct_val > 90:
            disk_color = "red"
        elif pct_val > 70:
            disk_color = "yellow"
        else:
            disk_color = "green"

        disk_bar = "[" + disk_color * pct_val + "[" * (100 - pct_val) + "]"
        disk_bar = disk_color[:1] * min(pct_val, 50) + " " * min(max(0, 50 - pct_val), 50)

        header_panel = Panel(
            Group(
                Text(f"{UI['disk']}: {disk['used']} {UI['used_of']} {disk['total']} ({disk['percent']})", style=f"bold {disk_color}"),
                Text(f"{UI['available']}: {disk['available']}", style="dim"),
            ),
            title=f"[bold]{UI['system']}[/]",
            border_style=disk_color,
            padding=(1, 2),
        )

        console.print()
        console.print(header_panel)
        console.print()
        console.print(table)
        console.print()

        console.print(
            Align.center(
                Text(UI["dashboard_hint"], style="dim"),
            )
        )

    # ---- CATEGORY VIEW ----
    def _show_category(self, category: str):
        if category not in self.results:
            console.print(f"[red]{UI['no_data']} {CATEGORY_LABELS.get(category, category)}[/]")
            return

        sr = self.results[category]
        sr.sort_by_size()
        total_pages = (len(sr.items) + self.page_size - 1) // self.page_size
        if self.current_page >= total_pages:
            self.current_page = max(0, total_pages - 1)

        start = self.current_page * self.page_size
        end = start + self.page_size
        page_items = sr.items[start:end]

        color = CATEGORY_COLORS.get(category, "white")
        label = CATEGORY_LABELS.get(category, category)

        # Ensure current_item is in valid range
        if self.current_item < 0:
            self.current_item = 0
        if self.current_item >= len(sr.items):
            self.current_item = len(sr.items) - 1

        table = Table(title=f"{label} ({format_bytes(sr.total_size)} | {UI['page']} {self.current_page + 1}/{total_pages})", box=box.ROUNDED)
        table.add_column(UI["category"], style="cyan", width=16)
        table.add_column(UI["selected"], width=16)
        table.add_column("Descripción", style="cyan")
        table.add_column(UI["size"], justify="right", style="cyan")
        table.add_column("Seguro", justify="center")
        table.add_column("Ruta", style="dim")

        for i, item in enumerate(page_items):
            idx = start + i
            sel = "[bold green]✓[/]" if item.selected else "[dim]  [/]"
            safe = f"[green]{UI['yes']}[/]" if item.safe_to_delete else f"[red]{UI['no']}[/]"
            path_display = item.path
            if len(path_display) > 50:
                path_display = "..." + path_display[-47:]

            is_current = (idx == self.current_item)
            key_display = " > " if is_current else "   "
            desc_style = f"bold cyan" if is_current else "cyan"
            desc_text = f"[{desc_style}]{item.description}[/]"

            table.add_row(
                f"[bold cyan]{key_display}{idx + 1}[/]",
                sel,
                desc_text,
                item.size_human,
                safe,
                path_display,
            )

        # Show cleanup action hint for selected items
        selected = [i for i in sr.items if i.selected]
        if selected:
            console.print()
            console.print(Rule(style="yellow"))
            console.print(Text(f"[bold yellow]{UI['selected']}: {format_bytes(sum(i.size for i in selected))}[/]", style="yellow"))
            for item in selected[:5]:
                if item.cleanup_action:
                    console.print(Text(f"  [dim]→[/] {item.cleanup_action}", style="dim cyan"))
                if item.cleanup_warning:
                    console.print(Text(f"  [dim]⚠[/] {item.cleanup_warning}", style="yellow"))
            if len(selected) > 5:
                console.print(Text(f"  ... {UI['and']} {len(selected) - 5} {UI['and_more']}", style="dim"))

        console.clear()
        self._print_header()
        console.print(table)
        console.print()
        console.print(
            Align.center(
                Text(UI["cleanup_hint"], style="dim"),
            )
        )

    def _show_cleanup_confirm(self):
        collected = []
        for cat in CATEGORY_ORDER:
            if cat in self.results:
                for item in self.results[cat].items:
                    if item.selected:
                        collected.append(item)

        if not collected:
            console.print(f"[yellow]{UI['no_items_selected']}[/]")
            return

        total = sum(i.size for i in collected)
        console.clear()
        self._print_header()

        console.print(Panel(
            Text(UI["permanently_delete"], style="bold yellow"),
            border_style="yellow",
        ))
        console.print()

        table = Table(box=box.ROUNDED)
        table.add_column(UI["category"], style="cyan")
        table.add_column("Descripción", style="white")
        table.add_column(UI["size"], justify="right", style="cyan")
        table.add_column("Seguro", justify="center")

        for item in collected:
            safe = "[green]Yes[/]" if item.safe_to_delete else "[red]No[/]"
            table.add_row(
                CATEGORY_LABELS.get(item.category, item.category),
                item.description,
                item.size_human,
                safe,
            )

        console.print(table)
        console.print()
        console.print(Panel(
            f"{UI['total_delete']}: [bold red]{format_bytes(total)}[/]",
            border_style="red",
        ))
        console.print()

        # Show cleanup actions and warnings
        any_action = any(i.cleanup_action for i in collected)
        any_warning = any(i.cleanup_warning for i in collected)
        if any_action or any_warning:
            console.print(Rule(f"[bold yellow]{UI['cleanup_details']}[/]", style="yellow"))
            for item in collected:
                if item.cleanup_action:
                    console.print(Text(f"  [bold cyan]→[/] {item.cleanup_action}", style="cyan"))
                if item.cleanup_warning:
                    console.print(Text(f"  [bold yellow]⚠[/] {item.cleanup_warning}", style="yellow"))
                console.print()

        console.print(Align.center(
            Text(f"[yellow]{UI['confirm_delete']}[/]  [bold red]Y/n[/]", style="dim"),
        ))

        # Wait for confirmation
        console.print()
        while True:
            key = readchar.readchar()
            if key in ("y", "Y"):
                return collected, total
            if key in ("n", "N", "\r", "\n", "\x03"):
                return None, None
            # Ignore other keys

    def _perform_cleanup(self, collected, total):
        if not collected:
            return

        disk_before = get_disk_usage()

        console.clear()
        self._print_header()

        success_count = 0
        fail_count = 0
        freed = 0
        deleted_paths = set()

        with Progress(
            TextColumn(f"[bold blue]{UI['cleaning']}[/]"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as p:
            task = p.add_task("", total=len(collected))
            for item in collected:
                ok, err = safe_delete(item.path)
                if ok:
                    success_count += 1
                    freed += item.size
                    deleted_paths.add(item.path)
                else:
                    fail_count += 1
                    console.print(f"  [red]✗ Failed: {item.path} - {err}[/]")
                p.update(task, advance=1)

        for cat in CATEGORY_ORDER:
            if cat in self.results:
                self.results[cat].items = [i for i in self.results[cat].items if i.path not in deleted_paths]
                self.results[cat].total_size = sum(i.size for i in self.results[cat].items)

        disk_after = get_disk_usage()
        console.print()
        console.print(Panel(
            Group(
                Text(f"{UI['deleted']}: [bold green]{success_count} {UI['items']}[/]", style="green"),
                Text(f"{UI['failed']}: [red]{fail_count}[/]", style="red" if fail_count > 0 else "green"),
                Text(f"{UI['freed']}: [bold green]{format_bytes(freed)}[/]"),
                Text(f"{UI['before']}: {disk_before.get('available', '?')}"),
                Text(f"{UI['after']}:  {disk_after.get('available', '?')}"),
            ),
            title=f"[bold green]{UI['cleanup_complete']}[/]",
            border_style="green",
            padding=(1, 2),
        ))
        console.print()

    # ---- MAIN LOOP ----
    def _main_loop(self):
        while True:
            key = self._read_key()
            key_raw = key

            if self.view_mode == "dashboard":
                self._handle_dashboard_key(key_raw)
            elif self.view_mode == "category":
                self._handle_category_key(key_raw)

    def _show_category_list(self):
        console.clear()
        self._print_header()

        visible_cats = [c for c in CATEGORY_ORDER if c in self.results and self.results[c].total_size > 0]
        if not visible_cats:
            console.print(f"[yellow]{UI['no_categories']}[/]")
            time.sleep(1)
            console.clear()
            self._show_dashboard()
            return

        if self.cat_list_index >= len(visible_cats):
            self.cat_list_index = len(visible_cats) - 1
        if self.cat_list_index < 0:
            self.cat_list_index = 0

        table = Table(title=UI["storage_by_category"], box=box.ROUNDED)
        table.add_column("Tecla", style="cyan", width=3)
        table.add_column(UI["category"], style="white")
        table.add_column(UI["size"], justify="right", style="cyan")
        table.add_column(UI["items"], justify="right", style="dim")

        grand_total = sum(sr.total_size for c in visible_cats for sr in [self.results[c]] if sr.total_size > 0)

        for i, cat in enumerate(visible_cats):
            sr = self.results[cat]
            size = sr.total_size
            count = len(sr.items)
            color = CATEGORY_COLORS.get(cat, "white")
            selected_marker = " > " if i == self.cat_list_index else "   "
            row_style = f"bold {color}" if i == self.cat_list_index else color
            table.add_row(
                f"[bold {row_style}]{selected_marker}{cat[:2].upper()}[/]",
                CATEGORY_LABELS.get(cat, cat),
                format_bytes(size),
                str(count),
            )

        console.print(table)
        console.print()
        console.print(Align.center(
            Text(UI["category_hint"], style="dim"),
        ))

        self._handle_category_list_key(self._read_key())


def main():
    manager = StorageManager()
    try:
        manager.run()
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
