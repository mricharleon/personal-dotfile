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
except ImportError:
    print("ERROR: rich required. Install with: pip install rich")
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

    @property
    def size_human(self) -> str:
        return format_bytes(self.size)

    @property
    def selected(self) -> bool:
        return getattr(self, '_selected', False)

    def toggle(self):
        self._selected = not self._selected


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
                    description=f"Large file ({format_bytes(size)})",
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
            }
            p.update(task, completed=1)
        return self.results

    def scan_xcode(self) -> ScanResult:
        r = ScanResult()
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
                    r.add(StorageItem(
                        path=path, size=size, category="xcode",
                        description=f"Xcode {name}",
                        safe_to_delete=name != "Profiles"
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
                                        description=f"Simulator: {d.get('name', 'Unknown')}",
                                        safe_to_delete=True
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
                    description="CoreSimulator data",
                    safe_to_delete=True
                ))
        return r

    def scan_docker(self) -> ScanResult:
        r = ScanResult()
        ok, out = run_cmd(["docker", "system", "df", "-v"])
        if ok:
            try:
                data = json.loads(out)
                desc_map = {
                    "Images": "Docker images",
                    "Containers": "Docker containers",
                    "Local Volumes": "Docker volumes",
                    "Build Cache": "Docker build cache",
                    "tmpfs": "Docker tmpfs",
                    "Proxy Cache": "Docker proxy cache",
                }
                for k, v in data.items():
                    if isinstance(v, dict) and "TotalSize" in v:
                        size = v.get("TotalSize", 0) or 0
                        if size > 10 * 1024 * 1024:
                            r.add(StorageItem(
                                path="docker://", size=size,
                                category="docker",
                                description=desc_map.get(k, f"Docker {k}"),
                                safe_to_delete=True
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
                    description="Docker local files",
                    safe_to_delete=True
                ))
        return r

    def scan_homebrew(self) -> ScanResult:
        r = ScanResult()
        dirs = {
            "Caches": str(self.home / "Library/Caches/Homebrew"),
            "Cask Caches": str(self.home / "Library/Caches/Homebrew/Cask"),
            "Linked": str(self.home / "Library/LinkedKegs"),
        }
        for name, path in dirs.items():
            if os.path.isdir(path):
                size = dir_size_fast(path)
                if size > 10 * 1024 * 1024:
                    r.add(StorageItem(
                        path=path, size=size, category="homebrew",
                        description=f"Homebrew {name}",
                        safe_to_delete=name != "Linked"
                    ))
        return r

    def scan_package_managers(self) -> ScanResult:
        r = ScanResult()
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
                    r.add(StorageItem(
                        path=path, size=size, category="package_managers",
                        description=f"{name}",
                        safe_to_delete=True
                    ))
        return r

    def scan_dev_caches(self) -> ScanResult:
        r = ScanResult()
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
                    r.add(StorageItem(
                        path=path, size=size, category="dev_caches",
                        description=f"Dev: {name}",
                        safe_to_delete=name not in ("Android SDK", "Android AVD")
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
                    description=f"{name} cache",
                    safe_to_delete=True
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
        dirs = {
            "System Logs": str(self.home / "Library/Logs"),
            "Crash Reports": str(self.home / "Library/Logs/DiagnosticReports"),
            "Temp files": "/tmp",
        }
        for name, path in dirs.items():
            if os.path.isdir(path):
                size = dir_size_fast(path)
                if size > 50 * 1024 * 1024:
                    r.add(StorageItem(
                        path=path, size=size, category="logs_temp",
                        description=name,
                        safe_to_delete=True
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
}

CATEGORY_LABELS = {
    "xcode": "Xcode",
    "docker": "Docker",
    "homebrew": "Homebrew",
    "package_managers": "Package Managers",
    "dev_caches": "Dev Tools Caches",
    "app_caches": "App Caches",
    "large_files": "Large Files (>500MB)",
    "ios_simulators": "iOS Simulators",
    "logs_temp": "Logs & Temp",
}

CATEGORY_ORDER = [
    "xcode", "docker", "homebrew", "package_managers",
    "dev_caches", "app_caches", "large_files", "ios_simulators", "logs_temp",
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
        self.page_size = 15
        self.view_mode = "dashboard"  # dashboard | category | cleanup
        self.selected_items = []

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

    def _print_header(self):
        console.print()
        console.print(Align.center(
            Text("mac-storage", style="bold cyan", font="mono"),
        ))
        console.print(Align.center(
            Text("Advanced Storage Manager for Developers", style="dim"),
        ))
        console.print()

    # ---- DASHBOARD ----
    def _show_dashboard(self):
        disk = get_disk_usage()
        if not disk:
            console.print("[red]Could not read disk usage.[/]")
            return

        # Build category summary
        table = Table(title="Storage by Category", box=box.ROUNDED)
        table.add_column("Category", style="cyan")
        table.add_column("Size", justify="right", style="white")
        table.add_column("Items", justify="right", style="dim")
        table.add_column("Share", justify="center")

        grand_total = 0
        cat_sizes = []
        for cat in CATEGORY_ORDER:
            if cat in self.results:
                sr = self.results[cat]
                if sr.total_size > 0:
                    cat_sizes.append((cat, sr.total_size, len(sr.items)))
                    grand_total += sr.total_size

        cat_sizes.sort(key=lambda x: x[1], reverse=True)

        for cat, size, count in cat_sizes:
            pct = (size / grand_total * 100) if grand_total > 0 else 0
            bar = "#" * int(pct / 2)
            color = CATEGORY_COLORS.get(cat, "white")
            table.add_row(
                f"[bold {color}]{CATEGORY_LABELS.get(cat, cat)}[/]",
                f"[bold white]{format_bytes(size)}[/]",
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
                Text(f"Disk: {disk['used']} used of {disk['total']} ({disk['percent']})", style=f"bold {disk_color}"),
                Text(f"Available: {disk['available']}", style="dim"),
            ),
            title="[bold]System[/]",
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
                Text("Press [bold green]ENTER[/] to explore categories | [bold red]Q[/] quit", style="dim"),
            )
        )

    # ---- CATEGORY VIEW ----
    def _show_category(self, category: str):
        if category not in self.results:
            console.print(f"[red]No data for {category}[/]")
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

        table = Table(title=f"{label} ({format_bytes(sr.total_size)} | page {self.current_page + 1}/{total_pages})", box=box.ROUNDED)
        table.add_column("#", style="dim", width=3)
        table.add_column("Selected", width=3)
        table.add_column("Description", style="white")
        table.add_column("Size", justify="right", style="cyan")
        table.add_column("Safe", justify="center")
        table.add_column("Path", style="dim")

        for i, item in enumerate(page_items):
            idx = start + i
            sel = "[bold green]✓[/]" if item.selected else "[dim]  [/]"
            safe = "[green]Yes[/]" if item.safe_to_delete else "[red]No[/]"
            path_display = item.path
            if len(path_display) > 50:
                path_display = "..." + path_display[-47:]
            table.add_row(
                str(idx + 1),
                sel,
                item.description,
                item.size_human,
                safe,
                path_display,
            )

        console.clear()
        self._print_header()
        console.print(table)
        console.print()
        console.print(
            Align.center(
                Text(
                    "↑↓ navigate | space select | a all | A none | p page- | n page+ | "
                    "[bold green]C[/] cleanup | [bold]B[/] back | [bold]Q[/] quit",
                    style="dim",
                ),
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
            console.print("[yellow]No items selected for cleanup.[/]")
            return

        total = sum(i.size for i in collected)
        console.clear()
        self._print_header()

        console.print(Panel(
            Text("This will permanently delete the following items.", style="bold yellow"),
            border_style="yellow",
        ))
        console.print()

        table = Table(box=box.ROUNDED)
        table.add_column("Category", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Size", justify="right", style="cyan")
        table.add_column("Safe", justify="center")

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
            f"Total to delete: [bold red]{format_bytes(total)}[/]",
            border_style="red",
        ))
        console.print()
        console.print(Align.center(
            Text("[bold red]Type YES to confirm deletion | any other key to cancel[/]", style="dim"),
        ))

    def _perform_cleanup(self):
        collected = []
        for cat in CATEGORY_ORDER:
            if cat in self.results:
                for item in self.results[cat].items:
                    if item.selected:
                        collected.append(item)

        if not collected:
            return

        total = sum(i.size for i in collected)
        disk_before = get_disk_usage()

        console.clear()
        self._print_header()

        success_count = 0
        fail_count = 0
        freed = 0

        with Progress(
            TextColumn("[bold blue]{task.description}[/]"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as p:
            task = p.add_task("Cleaning...", total=len(collected))
            for item in collected:
                ok, err = safe_delete(item.path)
                if ok:
                    success_count += 1
                    freed += item.size
                else:
                    fail_count += 1
                    console.print(f"  [red]✗ Failed: {item.path} - {err}[/]")
                p.update(task, advance=1)

        disk_after = get_disk_usage()
        console.print()
        console.print(Panel(
            Group(
                Text(f"Deleted: [bold green]{success_count} items[/]", style="green"),
                Text(f"Failed: [red]{fail_count}[/]", style="red" if fail_count > 0 else "green"),
                Text(f"Freed: [bold green]{format_bytes(freed)}[/]"),
                Text(f"Before: {disk_before.get('available', '?')} available"),
                Text(f"After:  {disk_after.get('available', '?')} available"),
            ),
            title="[bold green]Cleanup Complete[/]",
            border_style="green",
            padding=(1, 2),
        ))
        console.print()

    # ---- MAIN LOOP ----
    def _main_loop(self):
        while True:
            try:
                key = console.input("[bold cyan]> [/]")
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Goodbye![/]")
                break

            key = key.strip().lower()

            if key == "q":
                console.print("[dim]Goodbye![/]")
                break

            if key == "":
                # Show category list
                self._show_category_list()
                continue

            if key == "b" and self.view_mode != "dashboard":
                self.view_mode = "dashboard"
                self.current_category = None
                console.clear()
                self._show_dashboard()
                continue

            if key == "d":
                console.clear()
                self.view_mode = "dashboard"
                self.current_category = None
                self._show_dashboard()
                continue

            # Category navigation
            if self.view_mode == "category":
                if key == "n":
                    self.current_page += 1
                    self._show_category(self.current_category)
                elif key == "p":
                    self.current_page = max(0, self.current_page - 1)
                    self._show_category(self.current_category)
                elif key == "a":
                    if self.current_category in self.results:
                        for item in self.results[self.current_category].items:
                            item.toggle()
                    self._show_category(self.current_category)
                elif key == "A":
                    if self.current_category in self.results:
                        for item in self.results[self.current_category].items:
                            if item.selected:
                                item.toggle()
                    self._show_category(self.current_category)
                elif key == "c":
                    self._perform_cleanup()
                    self.view_mode = "dashboard"
                    self.current_category = None
                    console.clear()
                    self._show_dashboard()
                else:
                    # Try to select by number
                    try:
                        num = int(key)
                        if self.current_category in self.results:
                            items = self.results[self.current_category].items
                            if 1 <= num <= len(items):
                                items[num - 1].toggle()
                                self._show_category(self.current_category)
                    except ValueError:
                        pass
                continue

    def _show_category_list(self):
        console.clear()
        self._print_header()

        table = Table(title="Storage Categories", box=box.ROUNDED)
        table.add_column("Key", style="cyan", width=3)
        table.add_column("Category", style="white")
        table.add_column("Size", justify="right", style="cyan")
        table.add_column("Items", justify="right", style="dim")

        grand_total = 0
        cat_data = []
        for cat in CATEGORY_ORDER:
            if cat in self.results:
                sr = self.results[cat]
                if sr.total_size > 0:
                    grand_total += sr.total_size
                    cat_data.append((cat, sr.total_size, len(sr.items)))

        cat_data.sort(key=lambda x: x[1], reverse=True)

        for cat, size, count in cat_data:
            color = CATEGORY_COLORS.get(cat, "white")
            table.add_row(
                f"[bold {color}]{cat[:2].upper()}[/]",
                CATEGORY_LABELS.get(cat, cat),
                format_bytes(size),
                str(count),
            )

        console.print(table)
        console.print()
        console.print(Align.center(
            Text(
                "Press category key to explore | [bold]D[/] dashboard | [bold]Q[/] quit",
                style="dim",
            ),
        ))

        # Wait for key press
        try:
            key = console.input("[bold cyan]> [/]").strip().lower()
        except (KeyboardInterrupt, EOFError):
            key = "q"

        if key == "q":
            console.print("[dim]Goodbye![/]")
            return
        elif key == "d":
            console.clear()
            self._show_dashboard()
            return

        # Map key to category
        key_map = {
            "x": "xcode", "do": "docker", "ho": "homebrew", "pm": "package_managers",
            "dc": "dev_caches", "ac": "app_caches", "lf": "large_files",
            "is": "ios_simulators", "lt": "logs_temp",
            "xd": "xcode", "docker": "docker", "homebrew": "homebrew",
            "package": "package_managers", "dev": "dev_caches", "app": "app_caches",
            "large": "large_files", "sim": "ios_simulators", "log": "logs_temp",
        }

        # Direct match first
        cat = None
        for c in CATEGORY_ORDER:
            if key == c or key == c[:3]:
                cat = c
                break

        if not cat:
            # Try prefix matching
            matches = [c for c in CATEGORY_ORDER if c.startswith(key) or key in key_map and key_map[key] == c]
            if len(matches) == 1:
                cat = matches[0]
            elif len(matches) > 1:
                console.print(f"[yellow]Multiple matches: {', '.join(matches)}[/]")
                return

        if cat:
            self.view_mode = "category"
            self.current_category = cat
            self.current_page = 0
            self._show_category(cat)
        else:
            console.print(f"[yellow]Unknown category: {key}[/]")
            time.sleep(1)
            console.clear()
            self._show_dashboard()


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
