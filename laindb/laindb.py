__DOC__ = "This is the module that defines the commands of LainDB."

# Imports
import re
import os
import json
import shutil
from typing import Dict, List, Optional, Union

# Classes
class Lainconfig:
    @staticmethod
    def load_db(db_name):
        """
        Load or create a database.
        
        Args:
            db_name (str): Name of the database (folder name).
        
        Returns:
            Laindb: An instance of the database.
        """

        # Define the path to the 'instances' folder relative to the module's location
        module_dir = os.path.dirname(os.path.abspath(__file__))  # Pasta do módulo
        instances_folder = os.path.join(module_dir, "instances")  # Pasta 'instances' dentro do módulo

        database_folder = f"{instances_folder}/{db_name}"

        if not os.path.exists(database_folder):
            os.makedirs(database_folder)  # Create the database folder if it doesn't exist
        
        return Laindb(database_folder)

class Laindb:
    def __init__(self, database_folder):
        """
        Initialize the database.
        
        Args:
            database_folder (str): Path to the database folder.
        """
        self.database_folder = database_folder
    
    def create_table(self, table_name, columns: Optional[Dict[str, str]] = None):
        """
        Create a new table (subfolder) in the database.
        
        Args:
            table_name (str): Name of the table (subfolder name).
            columns (dict, optional): Dictionary defining column names and their types. Defaults to None.
        """
        table_folder = f"{self.database_folder}/{table_name}"
        if not os.path.exists(table_folder):
            os.makedirs(table_folder)  # Create the table folder if it doesn't exist

        # Create a JSON file to store the table's columns (schema)
        table_columns = f"{table_folder}/{table_name}_columns.json"
        if not os.path.exists(table_columns):
            with open(table_columns, 'w') as file:
                json.dump(columns if columns else {}, file)  # Save the columns (schema)

        # Create a JSON file to store the table's data
        table_data = f"{table_folder}/{table_name}_data.json"
        if not os.path.exists(table_data):
            with open(table_data, 'w') as file:
                json.dump([], file)  # Initialize with an empty list of records

    def _validate_schema(self, table_name, record: Dict):
        """
        Validate a record against the table's schema.
        
        Args:
            table_name (str): Name of the table.
            record (dict): Record to validate.
        
        Raises:
            ValueError: If the record does not match the schema.
        """
        table_columns_file = f"{self.database_folder}/{table_name}/{table_name}_columns.json"
        if not os.path.exists(table_columns_file):
            raise FileNotFoundError(f"The table '{table_name}' does not exist.")

        # Load the schema
        schema = self._load_data(table_columns_file)

        # Check if all required columns are present
        for column, column_type in schema.items():
            if column not in record:
                raise ValueError(f"Missing required column: '{column}'")
            if not isinstance(record[column], self._get_python_type(column_type)):
                raise ValueError(f"Invalid type for column '{column}'. Expected {column_type}, got {type(record[column]).__name__}")

    def _get_python_type(self, type_name: str):
        """
        Convert a type name to a Python type.
        
        Args:
            type_name (str): Name of the type (e.g., 'int', 'str').
        
        Returns:
            type: Python type.
        """
        type_mapping = {
            'int': int,
            'str': str,
            'bool': bool,
            'float': float,
            'list': list,
            'dict': dict,
        }
        return type_mapping.get(type_name, str)  # Default to str if type is unknown

    def insert(self, table_name, record: Dict):
        """
        Insert a new record into the specified table.
        
        Args:
            table_name (str): Name of the table.
            record (dict): Dictionary containing the record data.
        """
        table_data_file = f"{self.database_folder}/{table_name}/{table_name}_data.json"
        if not os.path.exists(table_data_file):
            raise FileNotFoundError(f"The table '{table_name}' does not exist.")

        # Validate the record against the schema
        self._validate_schema(table_name, record)

        data = self._load_data(table_data_file)
        data.append(record)  # Add the new record
        self._save_data(table_data_file, data)
    
    def add_column(self, table_name, column_name):
        """
        Add a new column to the table's schema and update all records.
        
        Args:
            table_name (str): Name of the table.
            column_name (str): Name of the new column.
        """
        table_columns_file = f"{self.database_folder}/{table_name}/{table_name}_columns.json"
        table_data_file = f"{self.database_folder}/{table_name}/{table_name}_data.json"

        if not os.path.exists(table_columns_file) or not os.path.exists(table_data_file):
            raise FileNotFoundError(f"The table '{table_name}' does not exist.")

        # Load the current columns
        columns = self._load_data(table_columns_file)
        if column_name in columns:
            raise ValueError(f"The column '{column_name}' already exists in the table.")

        # Add the new column to the schema
        columns.append(column_name)
        self._save_data(table_columns_file, columns)

        # Update all records to include the new column with a default value of None
        data = self._load_data(table_data_file)
        for record in data:
            record[column_name] = None
        self._save_data(table_data_file, data)

    def remove_column(self, table_name, column_name):
        """
        Remove a column from the table's schema and all records.
        
        Args:
            table_name (str): Name of the table.
            column_name (str): Name of the column to remove.
        """
        table_columns_file = f"{self.database_folder}/{table_name}/{table_name}_columns.json"
        table_data_file = f"{self.database_folder}/{table_name}/{table_name}_data.json"

        if not os.path.exists(table_columns_file) or not os.path.exists(table_data_file):
            raise FileNotFoundError(f"The table '{table_name}' does not exist.")

        # Load the current columns
        columns = self._load_data(table_columns_file)
        if column_name not in columns:
            raise ValueError(f"The column '{column_name}' does not exist in the table.")

        # Remove the column from the schema
        columns.remove(column_name)
        self._save_data(table_columns_file, columns)

        # Remove the column from all records
        data = self._load_data(table_data_file)
        for record in data:
            if column_name in record:
                del record[column_name]
        self._save_data(table_data_file, data)

    def find_all(self, table_name):
        """
        Retrieve all records from the specified table.
        
        Args:
            table_name (str): Name of the table.
        
        Returns:
            list: List of records.
        """
        table_data_file = f"{self.database_folder}/{table_name}/{table_name}_data.json"
        if not os.path.exists(table_data_file):
            raise FileNotFoundError(f"The table '{table_name}' does not exist.")

        return self._load_data(table_data_file)

    def find_by_id(self, table_name, record_id):
        """
        Find a record by its ID in the specified table.
        
        Args:
            table_name (str): Name of the table.
            record_id (int or str): ID of the record.
        
        Returns:
            dict: The record if found, otherwise None.
        """
        table_data_file = f"{self.database_folder}/{table_name}/{table_name}_data.json"
        if not os.path.exists(table_data_file):
            raise FileNotFoundError(f"The table '{table_name}' does not exist.")

        data = self._load_data(table_data_file)
        for record in data:
            if record.get('id') == record_id:
                return record
        return None

    def update(self, table_name, record_id, new_data: Dict):
        """
        Update a record in the specified table.
        
        Args:
            table_name (str): Name of the table.
            record_id (int or str): ID of the record.
            new_data (dict): Dictionary containing the updated data.
        
        Returns:
            bool: True if the record was updated, otherwise False.
        """
        table_data_file = f"{self.database_folder}/{table_name}/{table_name}_data.json"
        if not os.path.exists(table_data_file):
            raise FileNotFoundError(f"The table '{table_name}' does not exist.")

        data = self._load_data(table_data_file)
        for record in data:
            if record.get('id') == record_id:
                record.update(new_data)  # Update the record
                self._save_data(table_data_file, data)
                return True
        return False

    def delete(self, table_name, record_id):
        """
        Delete a record from the specified table.
        
        Args:
            table_name (str): Name of the table.
            record_id (int or str): ID of the record.
        
        Returns:
            bool: True if the record was deleted, otherwise False.
        """
        table_data_file = f"{self.database_folder}/{table_name}/{table_name}_data.json"
        if not os.path.exists(table_data_file):
            raise FileNotFoundError(f"The table '{table_name}' does not exist.")

        data = self._load_data(table_data_file)
        new_data = [record for record in data if record.get('id') != record_id]  # Filter out the record
        self._save_data(table_data_file, new_data)
        return len(new_data) != len(data)

    def query(self, table_name, conditions: Dict):
        """
        Query records from the specified table based on conditions.
        
        Args:
            table_name (str): Name of the table.
            conditions (dict): Dictionary of conditions (e.g., {'age': {'>': 25}}).
        
        Returns:
            list: List of records that match the conditions.
        """
        table_data_file = f"{self.database_folder}/{table_name}/{table_name}_data.json"
        if not os.path.exists(table_data_file):
            raise FileNotFoundError(f"The table '{table_name}' does not exist.")

        data = self._load_data(table_data_file)
        results = []

        for record in data:
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
        """
        Compare a value with a target using the specified operator.
        
        Args:
            value: Value to compare.
            operator (str): Comparison operator (e.g., '>', '==', 'LIKE').
            target: Target value to compare against.
        
        Returns:
            bool: True if the comparison is valid, otherwise False.
        """
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
        """
        Create a backup of the entire database.
        
        Args:
            backup_path (str): Path to save the backup file (e.g., 'backup.zip').
        """
        shutil.make_archive(backup_path.replace('.zip', ''), 'zip', self.database_folder)

    def restore(self, backup_path: str):
        """
        Restore the database from a backup.
        
        Args:
            backup_path (str): Path to the backup file (e.g., 'backup.zip').
        """
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file '{backup_path}' does not exist.")

        # Clear the current database folder
        if os.path.exists(self.database_folder):
            shutil.rmtree(self.database_folder)

        # Extract the backup
        shutil.unpack_archive(backup_path, self.database_folder, 'zip')

    def _load_data(self, file_path):
        """
        Load data from a JSON file.
        
        Args:
            file_path (str): Path to the JSON file.
        
        Returns:
            list: Data loaded from the file.
        """
        with open(file_path, 'r') as file:
            return json.load(file)

    def _save_data(self, file_path, data):
        """
        Save data to a JSON file.
        
        Args:
            file_path (str): Path to the JSON file.
            data (list): Data to save.
        """
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)