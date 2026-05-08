#!/usr/bin/env python3
"""POS CLI - Command line interface for the POS system."""

import argparse
import sys
import os
import signal
import logging
import subprocess
import time


def _run_with_reload(args):
    """Watch .py and .ui files, restart the app on changes."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("Install watchdog for --reload: pip install watchdog")
        sys.exit(1)

    logger = logging.getLogger("pos.reload")
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    project_dir = os.path.dirname(os.path.abspath(__file__))
    process = None

    def start_process():
        nonlocal process
        cmd = [sys.executable, "-u", __file__, "start"]
        if args.debug:
            cmd.append("--debug")
        env = os.environ.copy()
        env["POS_NO_RELOAD"] = "1"  # prevent child from also reloading
        process = subprocess.Popen(cmd, env=env)
        logger.info(f"Started POS (pid {process.pid})")

    def kill_process():
        nonlocal process
        if process and process.poll() is None:
            logger.info("Stopping POS...")
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
            process = None

    class ReloadHandler(FileSystemEventHandler):
        def __init__(self):
            self._last_reload = 0

        def on_modified(self, event):
            if event.is_directory:
                return
            path = event.src_path
            if not (path.endswith(".py") or path.endswith(".ui")):
                return
            # Debounce: ignore events within 1 second
            now = time.time()
            if now - self._last_reload < 1:
                return
            self._last_reload = now
            logger.info(f"Change detected: {os.path.relpath(path, project_dir)}")
            kill_process()
            start_process()

    handler = ReloadHandler()
    observer = Observer()
    observer.schedule(handler, project_dir, recursive=True)
    observer.start()
    logger.info(f"Watching {project_dir} for .py and .ui changes (auto-reload)")

    start_process()
    try:
        while True:
            if process and process.poll() is not None:
                logger.info("POS exited. Waiting for file changes to restart...")
                process = None
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Shutting down reload watcher...")
        kill_process()
        observer.stop()
    observer.join()


def cmd_start(args):
    """Start the POS application."""
    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        logging.debug("Debug mode enabled")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )

    # If --reload and not already a child process, run the watcher
    if getattr(args, 'reload', False) and not os.environ.get("POS_NO_RELOAD"):
        _run_with_reload(args)
        return

    logger = logging.getLogger("pos")
    logger.info("Starting POS application...")

    # ── Connect to database ───────────────────────────────────
    from database.connection import Database
    from config.settings import DATABASE, APP

    logger.debug(f"Database config: host={DATABASE['host']}, port={DATABASE['port']}, db={DATABASE['database']}")
    logger.debug(f"App config: {APP}")

    db = Database()
    if not db.connect():
        logger.error("Failed to connect to database. Check config/settings.py")
        sys.exit(1)

    logger.info("Database connected")
    db.init_tables()
    logger.info("Tables initialized")

    # ── Show login screen ─────────────────────────────────────
    from ui.login import LoginWindow
    from models.session import session

    # Try to restore existing session
    if session.restore(db):
        logger.info(f"Session restored for user: {session.username}")
    else:
        authenticated = False

        def on_login_success():
            nonlocal authenticated
            authenticated = True
            logger.info("Login successful")

        logger.info("Showing login screen...")
        login = LoginWindow(db=db, on_success=on_login_success)
        login.run()

        if not authenticated:
            logger.info("Login cancelled. Exiting.")
            db.disconnect()
            sys.exit(0)

    # ── Build main UI ─────────────────────────────────────────
    import tkinter as tk
    from tkinter import ttk
    from config.settings import APP as app_cfg
    from ui.dashboard_frame import DashboardFrame
    from ui.pos_frame import POSFrame
    from ui.product_frame import ProductFrame
    from ui.sales_frame import SalesFrame
    from ui.user_frame import UserFrame

    root = tk.Tk()
    root.title(app_cfg["title"])
    root.attributes("-zoomed", True)
    style = ttk.Style()
    style.theme_use(app_cfg["theme"])

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=5, pady=5)
    notebook.add(DashboardFrame(notebook, db), text="  Dashboard  ")
    notebook.add(POSFrame(notebook, db), text="  POS  ")
    notebook.add(ProductFrame(notebook, db), text="  Products  ")
    notebook.add(SalesFrame(notebook, db), text="  Sales  ")
    notebook.add(UserFrame(notebook, db), text="  Users  ")

    def on_close():
        logger.info("Shutting down POS...")
        db.disconnect()
        root.destroy()

    # Fast Ctrl+C: signal handler sets a flag checked by the event loop
    def _signal_handler(sig, frame):
        logger.info("Ctrl+C received")
        on_close()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    root.protocol("WM_DELETE_WINDOW", on_close)
    logger.info("UI ready")
    root.mainloop()


def cmd_db(args):
    """Database management commands."""
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger("pos.db")

    from database.connection import Database

    db = Database()
    if not db.connect():
        logger.error("Failed to connect to database.")
        sys.exit(1)

    if args.sync:
        logger.info("Syncing database tables...")
        db.init_tables()
        logger.info("Database tables synced successfully.")

    elif args.refresh:
        confirm = input("WARNING: This will DROP and recreate all tables. Data will be lost.\nType 'yes' to confirm: ")
        if confirm.strip().lower() != "yes":
            logger.info("Aborted.")
            db.disconnect()
            sys.exit(0)
        logger.info("Dropping existing tables...")
        drop_order = ["sale_items", "sales", "products", "categories"]
        for table in drop_order:
            try:
                db.execute_query(f"DROP TABLE IF EXISTS {table}")
                logger.info(f"  Dropped: {table}")
            except Exception as e:
                logger.warning(f"  Could not drop {table}: {e}")
        logger.info("Recreating tables...")
        db.init_tables()
        logger.info("Database refreshed successfully.")

    elif args.status:
        logger.info("Checking database status...")
        tables = db.fetch_all("SHOW TABLES")
        if tables:
            print(f"\nDatabase tables ({len(tables)}):")
            for t in tables:
                name = list(t.values())[0]
                count = db.fetch_one(f"SELECT COUNT(*) AS cnt FROM {name}")
                print(f"  {name:20s} {count['cnt']} rows")
        else:
            print("No tables found. Run: pos db --sync")

    else:
        logger.error("Specify an action: --sync, --refresh, or --status")
        sys.exit(1)

    db.disconnect()


def main():
    parser = argparse.ArgumentParser(
        prog="pos",
        description="POS System - Point of Sale CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # pos start
    start_parser = subparsers.add_parser("start", help="Start the POS application")
    start_parser.add_argument(
        "--debug", action="store_true", help="Run in debug mode with verbose logging"
    )
    start_parser.add_argument(
        "--reload", action="store_true",
        help="Auto-reload on .py/.ui file changes (requires watchdog)",
    )
    start_parser.set_defaults(func=cmd_start)

    # pos db
    db_parser = subparsers.add_parser("db", help="Database management")
    db_group = db_parser.add_mutually_exclusive_group()
    db_group.add_argument(
        "--sync", action="store_true", help="Create tables if they don't exist"
    )
    db_group.add_argument(
        "--refresh", action="store_true", help="Drop and recreate all tables (DESTRUCTIVE)"
    )
    db_group.add_argument(
        "--status", action="store_true", help="Show table status and row counts"
    )
    db_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    db_parser.set_defaults(func=cmd_db)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
