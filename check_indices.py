import sqlite3
from config import get_config
from pathlib import Path

config = get_config()
db_path = config.paths.db_path

print(f"Checking database at {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get indices for documentos table
cursor.execute("PRAGMA index_list(documentos)")
indices = cursor.fetchall()

print("\nIndices on 'documentos' table:")
for idx in indices:
    print(idx)
    # Check if unique
    is_unique = idx[2]
    if is_unique:
        print(f"  -> WARNING: Unique index found: {idx[1]}")
        cursor.execute(f"PRAGMA index_info({idx[1]})")
        cols = cursor.fetchall()
        print(f"     Columns: {[c[2] for c in cols]}")

conn.close()
