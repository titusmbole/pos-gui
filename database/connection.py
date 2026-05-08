import mysql.connector
from mysql.connector import Error
from config.settings import DATABASE


class Database:
    """Manages MySQL database connection and queries."""

    def __init__(self):
        self.connection = None

    def connect(self):
        """Establish connection to MySQL."""
        try:
            self.connection = mysql.connector.connect(
                host=DATABASE["host"],
                port=DATABASE["port"],
                user=DATABASE["user"],
                password=DATABASE["password"],
                database=DATABASE["database"],
            )
            if self.connection.is_connected():
                print("Connected to MySQL database")
                return True
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False

    def disconnect(self):
        """Close the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed")

    def execute_query(self, query, params=None):
        """Execute INSERT / UPDATE / DELETE queries."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            self.connection.rollback()
            print(f"Query error: {e}")
            raise
        finally:
            cursor.close()

    def fetch_all(self, query, params=None):
        """Execute SELECT and return all rows."""
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            print(f"Fetch error: {e}")
            raise
        finally:
            cursor.close()

    def fetch_one(self, query, params=None):
        """Execute SELECT and return one row."""
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except Error as e:
            print(f"Fetch error: {e}")
            raise
        finally:
            cursor.close()

    def init_tables(self):
        """Create tables if they don't exist."""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                barcode VARCHAR(50) UNIQUE,
                price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                stock INT NOT NULL DEFAULT 0,
                category_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
                    ON DELETE SET NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                total DECIMAL(10, 2) NOT NULL,
                payment_method VARCHAR(50) DEFAULT 'cash',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sale_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sale_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(10, 2) NOT NULL,
                subtotal DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id)
                    ON DELETE RESTRICT
            )
            """,
        ]
        for sql in tables:
            self.execute_query(sql)
        print("Database tables initialized")
