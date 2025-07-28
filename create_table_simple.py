#!/usr/bin/env python3
"""
シンプルなcancellation_historyテーブル作成スクリプト
"""

import os
import psycopg2
from dotenv import load_dotenv

def create_table():
    """cancellation_historyテーブルを作成"""
    
    # 環境変数を読み込み
    load_dotenv()
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URLが見つかりません")
        return False
    
    try:
        print("🔗 データベースに接続中...")
        print(f"URL: {database_url[:50]}...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("✅ 接続成功")
        
        # テーブルを作成
        print("🔨 cancellation_historyテーブルを作成中...")
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS cancellation_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            content_type VARCHAR(255) NOT NULL,
            cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
        
        cursor.execute(create_table_sql)
        print("✅ テーブル作成完了")
        
        # インデックスを作成
        print("📊 インデックスを作成中...")
        
        index_sqls = [
            "CREATE INDEX IF NOT EXISTS idx_cancellation_history_user_id ON cancellation_history(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_cancellation_history_content_type ON cancellation_history(content_type);",
            "CREATE INDEX IF NOT EXISTS idx_cancellation_history_user_content ON cancellation_history(user_id, content_type);"
        ]
        
        for sql in index_sqls:
            cursor.execute(sql)
        
        print("✅ インデックス作成完了")
        
        # 変更をコミット
        conn.commit()
        
        # テーブルが作成されたか確認
        print("🔍 テーブル作成を確認中...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'cancellation_history';
        """)
        
        result = cursor.fetchone()
        if result:
            print("✅ cancellation_historyテーブルが正常に作成されました！")
        else:
            print("❌ テーブル作成に失敗しました")
            return False
        
        cursor.close()
        conn.close()
        
        print("\n🎉 完了！Railwayダッシュボードでテーブルを確認してください。")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    print("🚀 cancellation_historyテーブル作成")
    print("=" * 40)
    create_table() 