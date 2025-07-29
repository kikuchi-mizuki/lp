#!/usr/bin/env python3
import os
import psycopg2

def check_railway_table_structure():
    """RailwayのPostgreSQLのテーブル構造を確認"""
    try:
        print("=== Railway PostgreSQLテーブル構造確認 ===")
        
        railway_db_url = os.getenv('RAILWAY_DATABASE_URL')
        if not railway_db_url:
            print("❌ RAILWAY_DATABASE_URL環境変数が設定されていません")
            return False
        
        print(f"📊 Railway PostgreSQLに接続中...")
        conn = psycopg2.connect(railway_db_url)
        c = conn.cursor()
        
        # テーブル一覧を確認
        c.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = c.fetchall()
        print(f"📋 テーブル一覧:")
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
        
        # subscription_periodsテーブルの構造を確認
        print(f"\n📋 subscription_periodsテーブルの構造:")
        c.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'subscription_periods'
            ORDER BY ordinal_position
        """)
        
        columns = c.fetchall()
        for column in columns:
            column_name, data_type, is_nullable, column_default = column
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            default = f"DEFAULT {column_default}" if column_default else ""
            print(f"  - {column_name}: {data_type} {nullable} {default}")
        
        # 他のテーブルの構造も確認
        for table_name in ['users', 'usage_logs', 'cancellation_history', 'user_states']:
            if table_name in [t[0] for t in tables]:
                print(f"\n📋 {table_name}テーブルの構造:")
                c.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = c.fetchall()
                for column in columns:
                    column_name, data_type, is_nullable, column_default = column
                    nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                    default = f"DEFAULT {column_default}" if column_default else ""
                    print(f"  - {column_name}: {data_type} {nullable} {default}")
        
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_railway_table_structure() 