#!/usr/bin/env python3
"""
企業管理テーブル詳細確認スクリプト
"""

from utils.db import get_db_connection, get_db_type

def check_company_tables():
    """企業管理テーブルの詳細を確認"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        print("=== 企業管理テーブル詳細確認 ===")
        
        # データベースタイプを確認
        db_type = get_db_type()
        print(f"データベースタイプ: {db_type}")
        
        # 企業管理テーブル一覧
        company_tables = [
            'companies',
            'company_line_accounts', 
            'company_payments',
            'company_contents',
            'company_notifications',
            'company_cancellations',
            'company_users'
        ]
        
        print(f"\n📋 企業管理テーブル一覧:")
        for table in company_tables:
            print(f"  - {table}")
        
        # 各テーブルの詳細確認
        for table in company_tables:
            print(f"\n🔍 {table}テーブルの詳細:")
            
            # テーブル構造確認
            if db_type == 'postgresql':
                c.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table,))
            else:
                c.execute("PRAGMA table_info(?)", (table,))
            
            columns = c.fetchall()
            
            if columns:
                print(f"  カラム数: {len(columns)}")
                print("  カラム詳細:")
                for col in columns:
                    if db_type == 'postgresql':
                        col_name, data_type, nullable, default = col
                        nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                        default_str = f" DEFAULT {default}" if default else ""
                        print(f"    - {col_name}: {data_type} {nullable_str}{default_str}")
                    else:
                        cid, name, type_name, not_null, default_val, pk = col
                        nullable_str = "NULL" if not not_null else "NOT NULL"
                        default_str = f" DEFAULT {default_val}" if default_val else ""
                        print(f"    - {name}: {type_name} {nullable_str}{default_str}")
                
                # レコード数確認
                c.execute(f"SELECT COUNT(*) FROM {table}")
                count = c.fetchone()[0]
                print(f"  レコード数: {count}")
                
                # 最新のレコードを表示（存在する場合）
                if count > 0:
                    c.execute(f"SELECT * FROM {table} ORDER BY created_at DESC LIMIT 3")
                    recent_records = c.fetchall()
                    print(f"  最新{len(recent_records)}件のレコード:")
                    for i, record in enumerate(recent_records, 1):
                        print(f"    {i}. {record}")
            else:
                print(f"  ❌ テーブル '{table}' が見つかりません")
        
        # 外部キー制約の確認
        print(f"\n🔗 外部キー制約の確認:")
        if db_type == 'postgresql':
            c.execute("""
                SELECT 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name LIKE 'company%'
                ORDER BY tc.table_name, kcu.column_name
            """)
        else:
            c.execute("PRAGMA foreign_key_list(companies)")
        
        foreign_keys = c.fetchall()
        
        if foreign_keys:
            print("  企業管理テーブルの外部キー:")
            for fk in foreign_keys:
                if db_type == 'postgresql':
                    table, column, foreign_table, foreign_column = fk
                    print(f"    - {table}.{column} -> {foreign_table}.{foreign_column}")
                else:
                    print(f"    - {fk}")
        else:
            print("  外部キー制約は設定されていません")
        
        # インデックスの確認
        print(f"\n📊 インデックスの確認:")
        if db_type == 'postgresql':
            c.execute("""
                SELECT 
                    tablename, 
                    indexname, 
                    indexdef
                FROM pg_indexes 
                WHERE tablename LIKE 'company%'
                ORDER BY tablename, indexname
            """)
        else:
            c.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'company%'")
        
        indexes = c.fetchall()
        
        if indexes:
            print("  企業管理テーブルのインデックス:")
            for idx in indexes:
                if db_type == 'postgresql':
                    table, index_name, index_def = idx
                    print(f"    - {table}.{index_name}: {index_def}")
                else:
                    print(f"    - {idx[0]}")
        else:
            print("  インデックスは設定されていません")
        
        conn.close()
        print(f"\n✅ 企業管理テーブル詳細確認完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_company_tables() 