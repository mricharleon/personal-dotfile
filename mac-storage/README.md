# mac-storage - Advanced Storage Manager for macOS Developers

Interactive TUI to analyze and clean up disk space on macOS. Designed for developers who accumulate storage with Xcode, Docker, package managers, and more.

## Requirements

- macOS
- Python 3.10+
- `rich` library

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python storage_manager.py
```

## Features

- **Dashboard** - Overview of disk usage by category with visual breakdown
- **9 Categories Scanned**:
  - Xcode (DerivedData, Archives, Simulators)
  - Docker (images, containers, volumes, build cache)
  - Homebrew (caches, cask caches)
  - Package Managers (npm, yarn, pip, cargo, go, gradle, maven, etc.)
  - Dev Tools (Flutter, Android, JetBrains, VSCode)
  - App Caches (browser caches, etc.)
  - Large Files (>500MB)
  - iOS Simulators
  - Logs & Temp files
- **Interactive cleanup** with confirmation before deletion
- **Safe mode** - marks non-safe items for review

## Controls

| Key | Action |
|-----|--------|
| `ENTER` | Explore categories |
| `D` | Return to dashboard |
| `B` | Go back |
| `Q` | Quit |
| `↑↓` | Navigate items |
| `Space` | Toggle item selection |
| `A` | Select all |
| `a` | Deselect all |
| `C` | Cleanup selected |
| `n` / `p` | Next / Previous page |

## Notes

- Items marked "No" for Safe require manual review before deletion
- Always review before running cleanup
- Some items may require appropriate permissions to delete
