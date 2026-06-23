#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def launch():
    # Get the absolute path of the project root
    root_dir = Path(__file__).parent.absolute()
    
    # Check for build types
    qt6_bin = root_dir / "debug" / "qcad-bin"
    qt5_bin = root_dir / "release" / "qcad-bin"
    
    bin_path = None
    qt_version = "Unknown"
    lib_path = ""

    if qt6_bin.exists():
        bin_path = qt6_bin
        qt_version = "6 (CMake/Ninja)"
        # For Qt 6 build, libraries are usually in debug/ or release/ AND plugins/
        lib_path = str(root_dir / "debug") + ":" + str(root_dir / "plugins")
    elif qt5_bin.exists():
        bin_path = qt5_bin
        qt_version = "5 (qmake/make)"
        lib_path = str(root_dir / "release") + ":" + str(root_dir / "plugins")
    else:
        print("Error: No QCAD binary found. Please ensure the project is built.")
        print(f"Checked: {qt6_bin}")
        print(f"Checked: {qt5_bin}")
        sys.exit(1)

    # Set up environment variables
    env = os.environ.copy()
    
    # Force X11 platform for better compatibility on Wayland systems
    env["QT_QPA_PLATFORM"] = "xcb"
    
    # Construct LD_LIBRARY_PATH
    ld_paths = lib_path.split(":")
    current_ld = env.get("LD_LIBRARY_PATH", "")
    if current_ld:
        ld_paths.append(current_ld)
    env["LD_LIBRARY_PATH"] = ":".join(ld_paths)
    
    # Handle the libpthread symbol issue often seen in certain Linux environments (e.g., Snap/Ubuntu)
    preload = "/lib/x86_64-linux-gnu/libpthread.so.0"
    if Path(preload).exists():
        env["LD_PRELOAD"] = preload

    print(f"--- QCAD Launcher ---")
    print(f"Using Qt Build: {qt_version}")
    print(f"Binary: {bin_path}")
    print(f"LD_LIBRARY_PATH: {env['LD_LIBRARY_PATH']}")
    if "LD_PRELOAD" in env:
        print(f"LD_PRELOAD: {env['LD_PRELOAD']}")
    print(f"----------------------")

    # Fork QCAD into its own process so the launcher can exit immediately.
    # Double-fork pattern: detaches QCAD completely from this process tree.
    pid = os.fork()
    if pid > 0:
        # Parent — QCAD is launched, we're done.
        print(f"QCAD started (pid {pid}). Launcher exiting.")
        sys.exit(0)

    # ── Child process ─────────────────────────────────────────────────
    # Become a new session leader so QCAD is fully independent.
    os.setsid()

    # Second fork — the grandchild runs QCAD, the child exits.
    # This prevents QCAD from ever reacquiring a controlling terminal.
    pid2 = os.fork()
    if pid2 > 0:
        os._exit(0)

    # ── Grandchild process (the actual QCAD) ──────────────────────────
    # Redirect stdout/stderr to /dev/null so orphaned output doesn't
    # pile up if launched from a .desktop file (no terminal).
    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, 0)  # stdin
    os.dup2(devnull, 1)  # stdout
    os.dup2(devnull, 2)  # stderr
    os.close(devnull)

    # Replace this process with qcad-bin — no leftover Python process.
    os.execvpe(str(bin_path), [str(bin_path)] + sys.argv[1:], env)


if __name__ == "__main__":
    launch()
