#!/usr/bin/env python3
"""
DATABASE_URL設定スクリプト
Railwayダッシュボードから取得したDATABASE_URLを設定します
"""

import os
import sys

def setup_database_url():
    """DATABASE_URLを設定"""
    
    print("🔧 DATABASE_URL設定スクリプト")
    print("=" * 40)
    
    print("\n📋 RailwayダッシュボードからDATABASE_URLを取得してください：")
    print("1. RailwayダッシュボードでPostgreSQLサービスを開く")
    print("2. 'Variables'タブを選択")
    print("3. 'DATABASE_URL'の値をコピー")
    print("4. 以下の入力欄に貼り付けてください")
    
    # ユーザーからDATABASE_URLを入力
    database_url = input("\nDATABASE_URLを入力してください: ").strip()
    
    if not database_url:
        print("❌ DATABASE_URLが入力されていません")
        return False
    
    if not database_url.startswith('postgresql://'):
        print("❌ 無効なDATABASE_URL形式です")
        print("postgresql://で始まるURLを入力してください")
        return False
    
    # .envファイルを作成または更新
    env_file = '.env'
    env_content = f"DATABASE_URL={database_url}\n"
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ DATABASE_URLを{env_file}に保存しました")
        
        # 環境変数としても設定
        os.environ['DATABASE_URL'] = database_url
        print("✅ 環境変数としても設定しました")
        
        return True
        
    except Exception as e:
        print(f"❌ ファイル保存エラー: {e}")
        return False

def test_connection():
    """データベース接続をテスト"""
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        load_dotenv()
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            print("❌ DATABASE_URLが見つかりません")
            return False
        
        print("\n🔗 データベース接続をテスト中...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # 接続テスト
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ 接続成功: {version[0]}")
        
        # 既存テーブルを確認
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 既存テーブル: {tables}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 接続テスト失敗: {e}")
        return False

def main():
    """メイン関数"""
    
    # DATABASE_URLを設定
    if not setup_database_url():
        sys.exit(1)
    
    # 接続テスト
    if not test_connection():
        print("\n❌ 接続テストに失敗しました")
        print("DATABASE_URLを確認してください")
        sys.exit(1)
    
    print("\n🎉 セットアップが完了しました！")
    print("次に 'python create_cancellation_table.py' を実行してください")

if __name__ == "__main__":
    main() 