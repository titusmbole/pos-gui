#!/usr/bin/env python3
"""POS CLI - Command line interface for the POS system."""

import argparse
import sys
import logging


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

    logger = logging.getLogger("pos")
    logger.info("Starting POS application...")

    # ── Show login screen first ───────────────────────────────
    from ui.login import LoginWindow

    authenticated = False

    def on_login_success():
        nonlocal authenticated
        authenticated = True
        logger.info("Login successful")

    logger.info("Showing login screen...")
    login = LoginWindow(on_success=on_login_success)
    login.run()

    if not authenticated:
        logger.info("Login cancelled. Exiting.")
        sys.exit(0)

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

    import tkinter as tk
    from tkinter import ttk
    from config.settings import APP as app_cfg
    from ui.pos_frame import POSFrame
    from ui.product_frame import ProductFrame
    from ui.sales_frame import SalesFrame

    root = tk.Tk()
    root.title(app_cfg["title"])
    root.geometry(f'{app_cfg["width"]}x{app_cfg["height"]}')
    style = ttk.Style()
    style.theme_use(app_cfg["theme"])

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=5, pady=5)
    notebook.add(POSFrame(notebook, db), text="  POS  ")
    notebook.add(ProductFrame(notebook, db), text="  Products  ")
    notebook.add(SalesFrame(notebook, db), text="  Sales  ")

    def on_close():
        logger.info("Shutting down POS...")
        db.disconnect()
        root.destroy()

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
