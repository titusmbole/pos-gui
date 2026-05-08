from database.connection import Database


class SaleModel:
    """Data operations for sales and sale items."""

    def __init__(self, db: Database):
        self.db = db

    def create_sale(self, total, payment_method, items):
        """
        Create a sale with its line items.
        items: list of dicts with product_id, quantity, unit_price, subtotal
        """
        sale_id = self.db.execute_query(
            "INSERT INTO sales (total, payment_method) VALUES (%s, %s)",
            (total, payment_method),
        )
        for item in items:
            self.db.execute_query(
                "INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, subtotal) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    sale_id,
                    item["product_id"],
                    item["quantity"],
                    item["unit_price"],
                    item["subtotal"],
                ),
            )
        return sale_id

    def get_all(self):
        return self.db.fetch_all(
            "SELECT * FROM sales ORDER BY created_at DESC"
        )

    def get_items(self, sale_id):
        return self.db.fetch_all(
            "SELECT si.*, p.name AS product_name "
            "FROM sale_items si "
            "JOIN products p ON si.product_id = p.id "
            "WHERE si.sale_id = %s",
            (sale_id,),
        )

    def get_daily_summary(self, date_str):
        return self.db.fetch_one(
            "SELECT COUNT(*) AS total_sales, COALESCE(SUM(total), 0) AS revenue "
            "FROM sales WHERE DATE(created_at) = %s",
            (date_str,),
        )
