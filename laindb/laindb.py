__DOC__ = "This is the module that defines the commands of LainDB."

import re
import os
import json
import shutil
from typing import Dict, List, Optional, Union


class Lainconfig:
    @staticmethod
    def load_db(db_name):
        module_dir = os.path.dirname(os.path.abspath(__file__))
        instances_folder = os.path.join(module_dir, "instances")
        database_folder = f"{instances_folder}/{db_name}"

        if not os.path.exists(database_folder):
            os.makedirs(database_folder)

        return Laindb(database_folder)


class Laindb:
    def __init__(self, database_folder):
        self.database_folder = database_folder
        self.cache = {}  # {table_name: {id: record}}

    def _load_to_cache(self, table_name):
        if table_name not in self.cache:
            table_data_file = f"{self.database_folder}/{table_name}/{table_name}_data.json"
            if not os.path.exists(table_data_file):
                raise FileNotFoundError(f"The table '{table_name}' does not exist.")
            data = self._load_data(table_data_file)
            self.cache[table_name] = {record['id']: record for record in data}

    def _save_cache(self, table_name):
        table_data_file = f"{self.database_folder}/{table_name}/{table_name}_data.json"
        data = list(self.cache[table_name].values())
        self._save_data(table_data_file, data)

    def create_table(self, table_name, columns: Optional[Dict[str, str]] = None):
        table_folder = f"{self.database_folder}/{table_name}"
        if not os.path.exists(table_folder):
            os.makedirs(table_folder)

        table_columns = f"{table_folder}/{table_name}_columns.json"
        if not os.path.exists(table_columns):
            with open(table_columns, 'w') as file:
                json.dump(columns if columns else {}, file)

        table_data = f"{table_folder}/{table_name}_data.json"
        if not os.path.exists(table_data):
            with open(table_data, 'w') as file:
                json.dump([], file)

    def _validate_schema(self, table_name, record: Dict):
        table_columns_file = f"{self.database_folder}/{table_name}/{table_name}_columns.json"
        if not os.path.exists(table_columns_file):
            raise FileNotFoundError(f"The table '{table_name}' does not exist.")
        schema = self._load_data(table_columns_file)
        for column, column_type in schema.items():
            if column not in record:
                raise ValueError(f"Missing required column: '{column}'")
            if not isinstance(record[column], self._get_python_type(column_type)):
                raise ValueError(f"Invalid type for column '{column}'. Expected {column_type}, got {type(record[column]).__name__}")

    def _get_python_type(self, type_name: str):
        type_mapping = {
            'int': int,
            'str': str,
            'bool': bool,
            'float': float,
            'list': list,
            'dict': dict,
        }
        return type_mapping.get(type_name, str)

    def insert(self, table_name, record: Dict):
        self._load_to_cache(table_name)
        self._validate_schema(table_name, record)
        self.cache[table_name][record['id']] = record
        self._save_cache(table_name)

    def add_column(self, table_name, column_name):
        table_columns_file = f"{self.database_folder}/{table_name}/{table_name}_columns.json"
        self._load_to_cache(table_name)
        columns = self._load_data(table_columns_file)
        if column_name in columns:
            raise ValueError(f"The column '{column_name}' already exists in the table.")
        columns[column_name] = 'str'
        self._save_data(table_columns_file, columns)
        for record in self.cache[table_name].values():
            record[column_name] = None
        self._save_cache(table_name)

    def remove_column(self, table_name, column_name):
        table_columns_file = f"{self.database_folder}/{table_name}/{table_name}_columns.json"
        self._load_to_cache(table_name)
        columns = self._load_data(table_columns_file)
        if column_name not in columns:
            raise ValueError(f"The column '{column_name}' does not exist in the table.")
        del columns[column_name]
        self._save_data(table_columns_file, columns)
        for record in self.cache[table_name].values():
            if column_name in record:
                del record[column_name]
        self._save_cache(table_name)

    def find_all(self, table_name):
        self._load_to_cache(table_name)
        return list(self.cache[table_name].values())

    def find_by_id(self, table_name, record_id):
        self._load_to_cache(table_name)
        return self.cache[table_name].get(record_id)

    def update(self, table_name, record_id, new_data: Dict):
        self._load_to_cache(table_name)
        if record_id in self.cache[table_name]:
            self.cache[table_name][record_id].update(new_data)
            self._save_cache(table_name)
            return True
        return False

    def delete(self, table_name, record_id):
        self._load_to_cache(table_name)
        if record_id in self.cache[table_name]:
            del self.cache[table_name][record_id]
            self._save_cache(table_name)
            return True
        return False

    def query(self, table_name, conditions: Dict):
        self._load_to_cache(table_name)
        results = []
        for record in self.cache[table_name].values():
            match = True
            for column, condition in conditions.items():
                if column not in record:
                    match = False
                    break
                for operator, value in condition.items():
                    if not self._compare(record[column], operator, value):
                        match = False
                        break
                if not match:
                    break
            if match:
                results.append(record)
        return results

    def _compare(self, value, operator: str, target):
        if operator == '==':
            return value == target
        elif operator == '!=':
            return value != target
        elif operator == '>':
            return value > target
        elif operator == '<':
            return value < target
        elif operator == '>=':
            return value >= target
        elif operator == '<=':
            return value <= target
        elif operator == 'LIKE':
            if not isinstance(target, str):
                return False
            return re.match(target.replace('%', '.*'), str(value)) is not None
        else:
            raise ValueError(f"Unsupported operator: '{operator}'")

    def backup(self, backup_path: str):
        shutil.make_archive(backup_path.replace('.zip', ''), 'zip', self.database_folder)

    def restore(self, backup_path: str):
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file '{backup_path}' does not exist.")
        if os.path.exists(self.database_folder):
            shutil.rmtree(self.database_folder)
        shutil.unpack_archive(backup_path, self.database_folder, 'zip')

    def _load_data(self, file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    def _save_data(self, file_path, data):
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
