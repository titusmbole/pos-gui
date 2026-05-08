# ImaraPOS

A Point of Sale system for small businesses built with Python, Tkinter, and MySQL.

## Features

- **Dashboard** — Daily sales summary, revenue, product count, low-stock alerts, and recent transactions
- **POS Checkout** — Product card grid with images, click-to-add cart, quantity adjustment (−/+), and delete per item
- **Payment Methods** — Cash (confirm dialog), Mpesa (phone number input), Card (bank selection)
- **Product Management** — Add/edit/delete products with image upload, barcode, pricing, stock, and categories
- **Sales History** — View all transactions with daily summaries
- **User Management** — Add/edit users, assign roles (Admin/Cashier), reset passwords, activate/deactivate accounts
- **Authentication** — Login screen with session persistence (auto-restore on restart)
- **Config File** — JSON-based configuration for database and app settings

## Requirements

- Python 3.10+
- MySQL 5.7+ or MariaDB 10.3+
- Tkinter (usually included with Python)

## Installation

```bash
# Clone the repository
git clone https://github.com/imaradesk/imarapos.git
cd imarapos

# Create virtual environment
python3 -m venv env
source env/bin/activate   # Linux/macOS
# env\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

## Configuration

Create a `config.json` file (a sample is included in the project root):

```json
{
    "appName": "ImaraPOS",
    "appVersion": "1.0.0",
    "appDescription": "A Point of Sale system for small businesses.",
    "appAuthor": "Titus Kilunda",
    "appLicense": "MIT",
    "database": {
        "host": "localhost",
        "port": 3306,
        "username": "root",
        "password": "",
        "name": "imarapos_db"
    }
}
```

Make sure the MySQL database exists before starting:

```sql
CREATE DATABASE imarapos_db;
```

## Usage

### Start the application

```bash
pos start --config config.json
```

Options:

| Flag | Description |
|------|-------------|
| `--config`, `-c` | Path to JSON config file |
| `--debug` | Enable verbose debug logging |
| `--reload` | Auto-reload on file changes (requires watchdog) |

### Database management

```bash
pos db --config config.json --sync      # Create tables if they don't exist
pos db --config config.json --status    # Show table status and row counts
pos db --config config.json --refresh   # Drop and recreate all tables (DESTRUCTIVE)
```

### Default login

On first run, an admin user is seeded automatically:

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin123` |

Change the password after first login.

## Building an Executable

Build a standalone executable for distribution using PyInstaller:

```bash
python build.py                          # Directory mode (default)
python build.py --onefile                # Single executable
python build.py --name MyPOS             # Custom name
python build.py --onefile --icon app.ico # With icon
```

The build script auto-detects the host OS (Linux, macOS, Windows) and configures PyInstaller accordingly. The built executable accepts the same CLI arguments:

```bash
./dist/ImaraPOS start --config config.json
```

## Project Structure

```
pos/
├── cli.py                # CLI entry point
├── build.py              # Build script (PyInstaller)
├── config.json           # App & database configuration
├── setup.py              # Package setup
├── requirements.txt      # Python dependencies
├── config/
│   └── settings.py       # Config loader
├── database/
│   └── connection.py     # MySQL connection manager
├── models/
│   ├── product.py        # Product CRUD
│   ├── sale.py           # Sale operations
│   ├── session.py        # User session (singleton)
│   └── user.py           # User CRUD & authentication
├── ui/
│   ├── login.py          # Login window
│   ├── dashboard_frame.py
│   ├── pos_frame.py      # POS checkout with card grid
│   ├── product_frame.py  # Product management
│   ├── sales_frame.py    # Sales history
│   ├── user_frame.py     # User management
│   ├── table.py          # Custom table widget
│   ├── add_product_dialog.py
│   ├── edit_product_dialog.py
│   └── add_user_dialog.py
└── uploads/              # Product images
```

## License

MIT
