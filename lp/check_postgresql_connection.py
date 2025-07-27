import os
import psycopg2
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

print('=== PostgreSQL接続テスト ===')

try:
    # ローカルPostgreSQL接続をテスト
    print('ローカルPostgreSQL接続をテスト中...')
    
    conn = psycopg2.connect(
        host="localhost",
        database="ai_collections",
        user="postgres",
        password="password"
    )
    
    print('✅ PostgreSQL接続成功')
    
    # テーブル一覧を確認
    c = conn.cursor()
    c.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    
    tables = c.fetchall()
    print(f'\nテーブル一覧 ({len(tables)}件):')
    for table in tables:
        print(f'  - {table[0]}')
    
    # ユーザーテーブルを確認
    if ('users',) in tables:
        c.execute("SELECT * FROM users LIMIT 5")
        users = c.fetchall()
        print(f'\nユーザー数: {len(users)}')
        for user in users:
            print(f'  ユーザー: {user}')
    
    # 使用量ログテーブルを確認
    if ('usage_logs',) in tables:
        c.execute("SELECT * FROM usage_logs LIMIT 5")
        logs = c.fetchall()
        print(f'\n使用量ログ数: {len(logs)}')
        for log in logs:
            print(f'  ログ: {log}')
    
    conn.close()
    
except Exception as e:
    print(f'❌ PostgreSQL接続エラー: {e}')
    
    # 代替接続情報を試す
    print('\n=== 代替接続情報を試行 ===')
    
    # 一般的なPostgreSQL接続情報
    connection_configs = [
        {
            'host': 'localhost',
            'database': 'postgres',
            'user': 'postgres',
            'password': 'postgres'
        },
        {
            'host': 'localhost',
            'database': 'ai_collections',
            'user': 'postgres',
            'password': 'postgres'
        },
        {
            'host': '127.0.0.1',
            'database': 'ai_collections',
            'user': 'postgres',
            'password': 'password'
        }
    ]
    
    for config in connection_configs:
        try:
            print(f'接続テスト: {config["host"]}/{config["database"]}')
            conn = psycopg2.connect(**config)
            print(f'✅ 接続成功: {config["host"]}/{config["database"]}')
            conn.close()
            break
        except Exception as e:
            print(f'❌ 接続失敗: {e}')
    
    print('\n=== 推奨設定 ===')
    print('PostgreSQLが使用されている場合は、.envファイルのDATABASE_URLを以下のように設定してください:')
    print('DATABASE_URL=postgresql://postgres:password@localhost/ai_collections') 