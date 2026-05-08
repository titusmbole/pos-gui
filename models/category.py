from database.connection import Database


class CategoryModel:
    """Data operations for categories."""

    def __init__(self, db: Database):
        self.db = db

    def get_all(self):
        return self.db.fetch_all("SELECT * FROM categories ORDER BY name")

    def add(self, name):
        return self.db.execute_query(
            "INSERT INTO categories (name) VALUES (%s)", (name,)
        )

    def update(self, category_id, name):
        self.db.execute_query(
            "UPDATE categories SET name=%s WHERE id=%s", (name, category_id)
        )

    def delete(self, category_id):
        self.db.execute_query("DELETE FROM categories WHERE id = %s", (category_id,))
