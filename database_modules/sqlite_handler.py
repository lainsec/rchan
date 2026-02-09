import sqlite3
import json
import os
from typing import Dict, List, Optional, Any, Union

class SQLiteHandler:
    def __init__(self, db_path):
        self.db_path = db_path
        self.column_types = {}  # {table_name: {col_name: type_str}}
        self._ensure_db_dir()

    def _ensure_db_dir(self):
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_table(self, table_name, columns: Dict[str, str]):
        self.column_types[table_name] = columns
        
        cols_def = []
        has_id = False
        
        for col, col_type in columns.items():
            sql_type = "TEXT"
            if col_type == 'int':
                sql_type = "INTEGER"
            elif col_type == 'float':
                sql_type = "REAL"
            
            if col == 'id':
                has_id = True
                cols_def.append(f"{col} {sql_type} PRIMARY KEY")
            else:
                cols_def.append(f"{col} {sql_type}")
        
        if not has_id:
            # LainDB requires 'id' for its operations (cache key), so we force it.
            cols_def.insert(0, "id INTEGER PRIMARY KEY")
        
        cols_str = ", ".join(cols_def)
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({cols_str})"
        
        with self._get_connection() as conn:
            conn.execute(query)

    def _serialize(self, table_name, record: Dict):
        """Convert list/dict to JSON strings for storage"""
        out = record.copy()
        columns = self.column_types.get(table_name, {})
        for k, v in record.items():
            col_type = columns.get(k)
            if col_type in ['list', 'dict'] and v is not None:
                out[k] = json.dumps(v)
        return out

    def _deserialize(self, table_name, row: sqlite3.Row):
        """Convert JSON strings back to list/dict"""
        out = dict(row)
        columns = self.column_types.get(table_name, {})
        for k, v in out.items():
            col_type = columns.get(k)
            if col_type in ['list', 'dict'] and isinstance(v, str):
                try:
                    out[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    pass # Keep as is if decode fails
        return out

    def insert(self, table_name, record: Dict):
        record = self._serialize(table_name, record)
        keys = list(record.keys())
        placeholders = ",".join(["?"] * len(keys))
        columns = ",".join(keys)
        values = [record[k] for k in keys]
        
        query = f"INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        with self._get_connection() as conn:
            conn.execute(query, values)

    def find_all(self, table_name):
        with self._get_connection() as conn:
            cursor = conn.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            return [self._deserialize(table_name, row) for row in rows]

    def find_by_id(self, table_name, record_id):
        with self._get_connection() as conn:
            cursor = conn.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            if row:
                return self._deserialize(table_name, row)
        return None

    def update(self, table_name, record_id, new_data: Dict):
        new_data = self._serialize(table_name, new_data)
        set_parts = []
        values = []
        for k, v in new_data.items():
            set_parts.append(f"{k} = ?")
            values.append(v)
        
        values.append(record_id)
        query = f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE id = ?"
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, values)
            return cursor.rowcount > 0

    def delete(self, table_name, record_id):
        with self._get_connection() as conn:
            cursor = conn.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
            return cursor.rowcount > 0

    def query(self, table_name, conditions: Dict):
        query = f"SELECT * FROM {table_name}"
        where_parts = []
        values = []
        
        for col, cond in conditions.items():
            for op, val in cond.items():
                sql_op = op
                if op == '==':
                    sql_op = '='
                
                where_parts.append(f"{col} {sql_op} ?")
                values.append(val)
        
        if where_parts:
            query += " WHERE " + " AND ".join(where_parts)
            
        with self._get_connection() as conn:
            cursor = conn.execute(query, values)
            rows = cursor.fetchall()
            return [self._deserialize(table_name, row) for row in rows]
            
    def add_column(self, table_name, column_name):
        # Default to TEXT as per generic add
        # LainDB adds as 'str'
        self.column_types[table_name][column_name] = 'str'
        try:
            with self._get_connection() as conn:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} TEXT")
        except sqlite3.OperationalError:
            # Column might already exist
            pass

    def remove_column(self, table_name, column_name):
        # SQLite doesn't support DROP COLUMN in older versions easily, 
        # but modern sqlite (3.35+) does: ALTER TABLE DROP COLUMN
        # We'll try it.
        if column_name in self.column_types.get(table_name, {}):
            del self.column_types[table_name][column_name]
            
        try:
            with self._get_connection() as conn:
                conn.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
        except sqlite3.OperationalError:
            # Fallback or ignore if not supported/column missing
            pass


class SQLiteConfig:
    @staticmethod
    def load_db(db_name):
        # Store databases in a 'databases' folder
        return SQLiteHandler(f"databases/{db_name}.db")
