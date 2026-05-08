from database.connection import Database


class ProductModel:
    """Data operations for products."""

    def __init__(self, db: Database):
        self.db = db

    def get_all(self):
        return self.db.fetch_all(
            "SELECT p.*, c.name AS category_name "
            "FROM products p "
            "LEFT JOIN categories c ON p.category_id = c.id "
            "ORDER BY p.name"
        )

    def search(self, keyword):
        like = f"%{keyword}%"
        return self.db.fetch_all(
            "SELECT p.*, c.name AS category_name "
            "FROM products p "
            "LEFT JOIN categories c ON p.category_id = c.id "
            "WHERE p.name LIKE %s OR p.barcode LIKE %s "
            "ORDER BY p.name",
            (like, like),
        )

    def get_by_barcode(self, barcode):
        return self.db.fetch_one(
            "SELECT * FROM products WHERE barcode = %s", (barcode,)
        )

    def get_by_id(self, product_id):
        return self.db.fetch_one(
            "SELECT * FROM products WHERE id = %s", (product_id,)
        )

    def add(self, name, barcode, price, stock, category_id, image=None):
        return self.db.execute_query(
            "INSERT INTO products (name, barcode, price, stock, category_id, image) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (name, barcode, price, stock, category_id, image),
        )

    def update(self, product_id, name, barcode, price, stock, category_id, image=None):
        if image is not None:
            self.db.execute_query(
                "UPDATE products SET name=%s, barcode=%s, price=%s, stock=%s, "
                "category_id=%s, image=%s WHERE id=%s",
                (name, barcode, price, stock, category_id, image, product_id),
            )
        else:
            self.db.execute_query(
                "UPDATE products SET name=%s, barcode=%s, price=%s, stock=%s, "
                "category_id=%s WHERE id=%s",
                (name, barcode, price, stock, category_id, product_id),
            )

    def update_stock(self, product_id, quantity_sold):
        self.db.execute_query(
            "UPDATE products SET stock = stock - %s WHERE id = %s",
            (quantity_sold, product_id),
        )

    def delete(self, product_id):
        self.db.execute_query("DELETE FROM products WHERE id = %s", (product_id,))
