#!/usr/bin/env python3
"""
Build script for ImaraPOS.
Detects the host OS and creates a standalone executable using PyInstaller.

Usage:
    python build.py                  # Build for current OS
    python build.py --onefile        # Single-file executable
    python build.py --name MyPOS     # Custom output name
"""

import os
import sys
import platform
import subprocess
import shutil


def detect_os():
    """Detect the base operating system."""
    system = platform.system().lower()
    if system == "linux":
        return "linux"
    elif system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        print(f"Warning: Unknown OS '{system}', building as generic.")
        return system


def ensure_pyinstaller():
    """Make sure PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} found.")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller installed.")


def build(onefile=False, app_name="ImaraPOS", icon=None):
    """Run PyInstaller to create the executable."""
    host_os = detect_os()
    project_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(project_dir, "dist")
    build_dir = os.path.join(project_dir, "build")
    entry_point = os.path.join(project_dir, "cli.py")

    print(f"Building for: {host_os} ({platform.machine()})")
    print(f"Python: {sys.version}")
    print(f"Entry point: {entry_point}")
    print(f"App name: {app_name}")

    ensure_pyinstaller()

    # Base PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", app_name,
        "--noconfirm",
        "--clean",
        "--distpath", dist_dir,
        "--workpath", build_dir,
    ]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    # Add data files: config, ui, models, database modules
    separator = ";" if host_os == "windows" else ":"

    data_dirs = ["config", "database", "models", "ui"]
    for d in data_dirs:
        src = os.path.join(project_dir, d)
        if os.path.isdir(src):
            cmd.append("--add-data")
            cmd.append(f"{src}{separator}{d}")

    # Include uploads directory (may contain product images)
    uploads = os.path.join(project_dir, "uploads")
    if os.path.isdir(uploads):
        cmd.append("--add-data")
        cmd.append(f"{uploads}{separator}uploads")

    # Hidden imports that PyInstaller may miss
    hidden_imports = [
        "mysql.connector",
        "mysql.connector.plugins",
        "mysql.connector.plugins.caching_sha2_password",
        "mysql.connector.plugins.mysql_native_password",
        "mysql.connector.locales",
        "mysql.connector.locales.eng",
        "mysql.connector.locales.eng.client_error",
        "mysql.connector.connection",
        "mysql.connector.network",
        "PIL",
        "PIL.Image",
        "PIL.ImageTk",
        "tkinter",
        "tkinter.ttk",
    ]
    for mod in hidden_imports:
        cmd.append("--hidden-import")
        cmd.append(mod)

    # Collect all submodules to ensure nothing is missed
    collect_all = ["mysql.connector", "PIL"]
    for pkg in collect_all:
        cmd.extend(["--collect-submodules", pkg])
        cmd.extend(["--collect-data", pkg])

    # Collect all tkinter data (TCL/TK libraries bundled with Python)
    cmd.extend(["--collect-all", "tkinter"])

    # OS-specific options
    if host_os == "windows":
        cmd.append("--console")  # Keep console for CLI args
        if icon and os.path.isfile(icon):
            cmd.append("--icon")
            cmd.append(icon)
    elif host_os == "macos":
        cmd.append("--console")
        if icon and os.path.isfile(icon):
            cmd.append("--icon")
            cmd.append(icon)
    else:
        # Linux
        cmd.append("--console")

    # Entry point
    cmd.append(entry_point)

    print(f"\nRunning: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"\nBuild FAILED (exit code {result.returncode})")
        sys.exit(1)

    # Determine output path
    if onefile:
        ext = ".exe" if host_os == "windows" else ""
        output = os.path.join(dist_dir, f"{app_name}{ext}")
    else:
        output = os.path.join(dist_dir, app_name)

    print(f"\nBuild SUCCESS!")
    print(f"OS:     {host_os} ({platform.machine()})")
    print(f"Output: {output}")
    print(f"\nUsage:")
    print(f"  {output} start --config config.json")
    print(f"  {output} start --config config.json --debug")
    print(f"  {output} db --config config.json --sync")

    # Copy a sample config next to the executable
    sample_src = os.path.join(project_dir, "config.json")
    if os.path.isfile(sample_src):
        if onefile:
            sample_dst = os.path.join(dist_dir, "config.json")
        else:
            sample_dst = os.path.join(dist_dir, app_name, "config.json")
        shutil.copy2(sample_src, sample_dst)
        print(f"  Copied config.json to {sample_dst}")

    # Clean up PyInstaller artifacts (keep only dist/)
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)
        print(f"  Cleaned up: {build_dir}/")

    spec_file = os.path.join(project_dir, f"{app_name}.spec")
    if os.path.isfile(spec_file):
        os.remove(spec_file)
        print(f"  Cleaned up: {spec_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build ImaraPOS executable")
    parser.add_argument(
        "--onefile", action="store_true",
        help="Package into a single executable file",
    )
    parser.add_argument(
        "--name", type=str, default="ImaraPOS",
        help="Name of the output executable (default: ImaraPOS)",
    )
    parser.add_argument(
        "--icon", type=str, default=None,
        help="Path to icon file (.ico for Windows, .icns for macOS)",
    )
    args = parser.parse_args()
    build(onefile=args.onefile, app_name=args.name, icon=args.icon)


if __name__ == "__main__":
    main()
