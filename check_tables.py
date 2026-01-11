#!/usr/bin/env python
"""Quick script to check database tables"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE 'hymns%' 
    ORDER BY table_name;
""")

tables = [row[0] for row in cursor.fetchall()]

print("\n=== Hymns App Tables in Database ===")
if tables:
    for table in tables:
        print(f"  [OK] {table}")
else:
    print("  [X] No hymns tables found!")

print("\n=== All Django Tables ===")
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name;
""")
all_tables = [row[0] for row in cursor.fetchall()]
for table in all_tables:
    print(f"  - {table}")

