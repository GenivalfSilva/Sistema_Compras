#!/usr/bin/env python
"""
Script to inspect V1 database schema and show exact column names
"""
import sqlite3
import os

def inspect_v1_schema():
    """Inspects the V1 database schema"""
    db_path = r"c:\Users\leonardo.fragoso\Desktop\Projetos\Sistema_Compras\Sistemas_Compras_V2\backend\db\sistema_compras_v1.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("📋 V1 DATABASE SCHEMA ANALYSIS")
    print("="*50)
    
    for table in tables:
        if table == 'sqlite_sequence':
            continue
            
        print(f"\n🔍 TABLE: {table}")
        print("-" * 30)
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        for col in columns:
            cid, name, type_name, notnull, default_val, pk = col
            pk_str = " (PK)" if pk else ""
            null_str = " NOT NULL" if notnull else ""
            default_str = f" DEFAULT {default_val}" if default_val else ""
            print(f"  {name}: {type_name}{pk_str}{null_str}{default_str}")
        
        # Show sample data
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  📊 Records: {count}")
        
        if count > 0:
            cursor.execute(f"SELECT * FROM {table} LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                print(f"  📝 Sample: {sample[:3]}..." if len(sample) > 3 else f"  📝 Sample: {sample}")
    
    conn.close()
    print("\n✅ Schema analysis complete!")

if __name__ == '__main__':
    inspect_v1_schema()
