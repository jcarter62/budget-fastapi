from .db_connector import DB, DBError
from dotenv import load_dotenv
import os

load_dotenv()

class Data:

    def __init__(self):
        self.db = DB()
        self.gl_list = []
        self.actual_items = []

    def __del__(self):
        if self.db and self.db.connection:
            self.db.connection.close()
        if self.db:
            self.db = None
        return

    def load_gl_list(self):
        # load sql text from file based on APP_ROOT / sql
        # sql file name is 01-gl-listing.sql
        app_root = os.getenv("APP_ROOT", "./")
        sql_path = os.path.join(app_root, "sql", "01-gl-listing.sql")
        if os.path.exists(sql_path):
            with open(sql_path, "r") as f:
                sql = f.read()
            try:
                cursor = self.db.connection.cursor()
                results = cursor.execute(sql)
                results = [self.db.extract_row(row) for row in results]
                self.gl_list = results
            except DBError as e:
                print(f"Error executing SQL from file: {e.message}")
        return self.gl_list

    def load_actual_items(self):
        app_root = os.getenv("APP_ROOT", "./")
        sql_path = os.path.join(app_root, "sql", "02-actual-items.sql")
        results = []
        if os.path.exists(sql_path):
            with open(sql_path, "r") as f:
                sql = f.read()
            try:
                cursor = self.db.connection.cursor()
                rows = cursor.execute(sql)
                results = [self.db.extract_row(row) for row in rows]
                self.actual_items = results
            except DBError as e:
                print(f"Error executing SQL from file: {e.message}")
        return self.actual_items

    def load_budget_import(self):
        app_root = os.getenv("APP_ROOT", "./")
        sql_path = os.path.join(app_root, "sql", "04-budget.sql")
        results = []
        if os.path.exists(sql_path):
            with open(sql_path, "r") as f:
                sql = f.read()
            try:
                cursor = self.db.connection.cursor()
                rows = cursor.execute(sql)
                results = [self.db.extract_row(row) for row in rows]
            except DBError as e:
                print(f"Error executing SQL from file: {e.message}")
        return results
