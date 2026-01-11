#!/usr/bin/env python
"""Check hymns_hymn table structure and data"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Check table structure
print("=== hymns_hymn Table Structure ===")
cursor.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'hymns_hymn'
    ORDER BY ordinal_position;
""")
columns = cursor.fetchall()
for col in columns:
    col_name, data_type, max_len = col
    if max_len:
        print(f"  {col_name}: {data_type}({max_len})")
    else:
        print(f"  {col_name}: {data_type}")

# Check row count
print("\n=== Data Count ===")
cursor.execute("SELECT COUNT(*) FROM hymns_hymn;")
count = cursor.fetchone()[0]
print(f"  Total hymns: {count}")

if count > 0:
    print("\n=== Sample Hymns (first 5) ===")
    cursor.execute("SELECT id, number, title FROM hymns_hymn ORDER BY number LIMIT 5;")
    hymns = cursor.fetchall()
    for hymn in hymns:
        print(f"  ID: {hymn[0]}, Number: {hymn[1]}, Title: {hymn[2]}")
else:
    print("\n  [INFO] No hymns in database yet. Use Django admin to add hymns!")



