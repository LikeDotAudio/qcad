#!/usr/bin/env python3
"""
QCAD Installer — sets up desktop launcher, icon, and optional CLI access.

Usage:
    python3 Install.py              # Install (interactive)
    python3 Install.py --install    # Install (non-interactive, defaults)
    python3 Install.py --uninstall  # Remove everything installed by this script
"""

import os
import sys
import shutil
import subprocess
import textwrap
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.absolute()
LAUNCH_SCRIPT = PROJECT_ROOT / "LAUNCH_QCAD.py"

# Icon sources (prefer SVG, fall back to PNG)
ICON_SVG = PROJECT_ROOT / "scripts" / "qcad_icon.svg"
ICON_PNG = PROJECT_ROOT / "scripts" / "qcad_icon.png"

# XDG standard install locations (user-level, no sudo needed)
DESKTOP_DIR = Path.home() / ".local" / "share" / "applications"
ICON_DIR_SVG = Path.home() / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps"
ICON_DIR_PNG = Path.home() / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps"
BIN_DIR = Path.home() / ".local" / "bin"

DESKTOP_FILE = DESKTOP_DIR / "qcad-custom.desktop"
INSTALLED_ICON_SVG = ICON_DIR_SVG / "qcad.svg"
INSTALLED_ICON_PNG = ICON_DIR_PNG / "qcad.png"
CLI_LINK = BIN_DIR / "qcad"

# ─── Desktop entry template ──────────────────────────────────────────────────

DESKTOP_ENTRY = textwrap.dedent("""\
    [Desktop Entry]
    Name=QCAD - APK FORK
    StartupWMClass=QCAD
    GenericName=CAD Software
    Comment=A 2D CAD System
    Exec={python} {launch_script} %F
    Path={project_root}
    Icon={icon_name}
    Terminal=false
    Type=Application
    Categories=Graphics;VectorGraphics;Engineering;Construction;2DGraphics;Science;
    MimeType=application/dxf;image/vnd.dxf;
    StartupNotify=true
""")

# ─── Helpers ──────────────────────────────────────────────────────────────────

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def info(msg):
    print(f"  {GREEN}✓{RESET} {msg}")


def warn(msg):
    print(f"  {YELLOW}⚠{RESET} {msg}")


def error(msg):
    print(f"  {RED}✗{RESET} {msg}")


def ask_yes_no(prompt, default=True):
    """Ask a yes/no question. Returns True/False."""
    hint = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"  {prompt} {hint} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if not answer:
        return default
    return answer.startswith("y")


def find_python():
    """Return the absolute path to the Python 3 interpreter."""
    return shutil.which("python3") or shutil.which("python") or sys.executable


def update_desktop_database():
    """Refresh the desktop file database so the launcher appears immediately."""
    try:
        subprocess.run(
            ["update-desktop-database", str(DESKTOP_DIR)],
            capture_output=True,
        )
    except FileNotFoundError:
        pass  # Not installed on all distros; non-critical


def update_icon_cache():
    """Refresh the icon cache so the icon appears immediately."""
    icon_base = Path.home() / ".local" / "share" / "icons" / "hicolor"
    try:
        subprocess.run(
            ["gtk-update-icon-cache", "-f", "-t", str(icon_base)],
            capture_output=True,
        )
    except FileNotFoundError:
        pass  # Non-critical


# ─── Pre-flight checks ───────────────────────────────────────────────────────

def preflight():
    """Verify the project is in a usable state."""
    errors = []

    if not LAUNCH_SCRIPT.exists():
        errors.append(f"Launch script not found: {LAUNCH_SCRIPT}")

    qt6_bin = PROJECT_ROOT / "debug" / "qcad-bin"
    qt5_bin = PROJECT_ROOT / "release" / "qcad-bin"
    if not qt6_bin.exists() and not qt5_bin.exists():
        errors.append(
            "No QCAD binary found. Build the project first.\n"
            f"    Checked: {qt6_bin}\n"
            f"    Checked: {qt5_bin}"
        )

    if not ICON_SVG.exists() and not ICON_PNG.exists():
        errors.append("No icon file found in scripts/ (looked for qcad_icon.svg and qcad_icon.png)")

    if errors:
        print(f"\n{RED}{BOLD}Pre-flight checks failed:{RESET}\n")
        for e in errors:
            error(e)
        print()
        sys.exit(1)


# ─── Install ──────────────────────────────────────────────────────────────────

def install(interactive=True):
    """Install QCAD desktop launcher, icon, and optional CLI link."""

    print(f"\n{BOLD}╔══════════════════════════════════════╗{RESET}")
    print(f"{BOLD}║        QCAD Installer for Linux      ║{RESET}")
    print(f"{BOLD}╚══════════════════════════════════════╝{RESET}\n")

    preflight()

    python_path = find_python()
    print(f"  Project root : {PROJECT_ROOT}")
    print(f"  Python       : {python_path}")
    print()

    # ── 1. Install icon ──────────────────────────────────────────────────────

    print(f"{BOLD}[1/3] Installing icon{RESET}")

    if ICON_SVG.exists():
        ICON_DIR_SVG.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ICON_SVG, INSTALLED_ICON_SVG)
        info(f"SVG icon → {INSTALLED_ICON_SVG}")

    if ICON_PNG.exists():
        ICON_DIR_PNG.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ICON_PNG, INSTALLED_ICON_PNG)
        info(f"PNG icon → {INSTALLED_ICON_PNG}")

    # Use "qcad" as the icon name so the system resolves from hicolor theme
    icon_name = "qcad"
    update_icon_cache()
    print()

    # ── 2. Create .desktop file ──────────────────────────────────────────────

    print(f"{BOLD}[2/3] Creating desktop launcher{RESET}")

    DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
    desktop_content = DESKTOP_ENTRY.format(
        python=python_path,
        launch_script=LAUNCH_SCRIPT,
        project_root=PROJECT_ROOT,
        icon_name=icon_name,
    )
    DESKTOP_FILE.write_text(desktop_content)
    DESKTOP_FILE.chmod(0o755)
    update_desktop_database()
    info(f"Desktop file → {DESKTOP_FILE}")
    print()

    # ── 3. Optional CLI symlink ──────────────────────────────────────────────

    print(f"{BOLD}[3/3] Command-line access{RESET}")

    create_link = True
    if interactive:
        create_link = ask_yes_no(
            f"Create 'qcad' command in {BIN_DIR}?", default=True
        )

    if create_link:
        BIN_DIR.mkdir(parents=True, exist_ok=True)

        # Create a small wrapper script so `qcad` works from anywhere
        wrapper = (
            f"#!/bin/sh\n"
            f'exec {python_path} "{LAUNCH_SCRIPT}" "$@"\n'
        )
        CLI_LINK.write_text(wrapper)
        CLI_LINK.chmod(0o755)
        info(f"CLI wrapper → {CLI_LINK}")

        # Check if ~/.local/bin is in PATH
        path_dirs = os.environ.get("PATH", "").split(":")
        if str(BIN_DIR) not in path_dirs:
            warn(
                f"{BIN_DIR} is not in your PATH.\n"
                "       Add this to your ~/.bashrc or ~/.profile:\n"
                f'       export PATH="$HOME/.local/bin:$PATH"'
            )
    else:
        info("Skipped CLI link.")

    print()
    print(f"{GREEN}{BOLD}  ✅ Installation complete!{RESET}")
    print()
    print("  • Search for \"QCAD\" in your application menu to launch.")
    print("  • Right-click the icon in the taskbar → Pin/Add to Favorites.")
    if create_link:
        print("  • Or run 'qcad' from a terminal.")
    print()


# ─── Uninstall ────────────────────────────────────────────────────────────────

def uninstall():
    """Remove everything installed by this script."""

    print(f"\n{BOLD}╔══════════════════════════════════════╗{RESET}")
    print(f"{BOLD}║       QCAD Uninstaller for Linux     ║{RESET}")
    print(f"{BOLD}╚══════════════════════════════════════╝{RESET}\n")

    removed = False

    for path, label in [
        (DESKTOP_FILE, "Desktop launcher"),
        (INSTALLED_ICON_SVG, "SVG icon"),
        (INSTALLED_ICON_PNG, "PNG icon"),
        (CLI_LINK, "CLI wrapper"),
    ]:
        if path.exists():
            path.unlink()
            info(f"Removed {label}: {path}")
            removed = True
        else:
            warn(f"{label} not found (already removed?): {path}")

    update_desktop_database()
    update_icon_cache()

    if removed:
        print(f"\n{GREEN}{BOLD}  ✅ Uninstall complete.{RESET}\n")
    else:
        print(f"\n  Nothing to remove — QCAD was not installed.\n")


# ─── CLI entry point ─────────────────────────────────────────────────────────

def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower().strip("-")
        if arg == "uninstall":
            uninstall()
        elif arg == "install":
            install(interactive=False)
        elif arg in ("h", "help"):
            print(__doc__)
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print(__doc__)
            sys.exit(1)
    else:
        install(interactive=True)


if __name__ == "__main__":
    main()
