#!/usr/bin/env python3
"""
cancellation_historyテーブル作成スクリプト
Railway PostgreSQLデータベースに直接接続してテーブルを作成します
"""

import os
import psycopg2
from dotenv import load_dotenv
import sys

def create_cancellation_history_table():
    """cancellation_historyテーブルを作成"""
    
    # 環境変数を読み込み
    load_dotenv()
    
    # データベース接続情報を取得
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL環境変数が見つかりません")
        print("以下の手順で設定してください：")
        print("1. RailwayダッシュボードでPostgreSQLサービスを開く")
        print("2. 'Variables'タブでDATABASE_URLをコピー")
        print("3. .envファイルに設定するか、環境変数として設定")
        return False
    
    try:
        # データベースに接続
        print("🔗 データベースに接続中...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # 既存のテーブル一覧を確認
        print("📋 既存のテーブルを確認中...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"既存のテーブル: {existing_tables}")
        
        # cancellation_historyテーブルが既に存在するかチェック
        if 'cancellation_history' in existing_tables:
            print("✅ cancellation_historyテーブルは既に存在します")
            return True
        
        # cancellation_historyテーブルを作成
        print("🔨 cancellation_historyテーブルを作成中...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cancellation_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                content_type VARCHAR(255) NOT NULL,
                cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        
        # インデックスを作成
        print("📊 インデックスを作成中...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cancellation_history_user_id 
            ON cancellation_history(user_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cancellation_history_content_type 
            ON cancellation_history(content_type);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cancellation_history_user_content 
            ON cancellation_history(user_id, content_type);
        """)
        
        # 変更をコミット
        conn.commit()
        
        # 作成されたテーブルの構造を確認
        print("🔍 テーブル構造を確認中...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'cancellation_history'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n📋 cancellation_historyテーブル構造:")
        print("列名\t\tデータ型\t\tNULL許可\tデフォルト値")
        print("-" * 60)
        for column in columns:
            print(f"{column[0]}\t\t{column[1]}\t\t{column[2]}\t\t{column[3]}")
        
        # テストデータを挿入して動作確認
        print("\n🧪 テストデータを挿入して動作確認...")
        cursor.execute("""
            INSERT INTO cancellation_history (user_id, content_type)
            VALUES (1, 'AI経理秘書')
            ON CONFLICT DO NOTHING;
        """)
        
        # テストデータを確認
        cursor.execute("""
            SELECT * FROM cancellation_history 
            WHERE content_type = 'AI経理秘書';
        """)
        
        test_data = cursor.fetchall()
        if test_data:
            print("✅ テストデータの挿入・取得が正常に動作しました")
            
            # テストデータを削除
            cursor.execute("""
                DELETE FROM cancellation_history 
                WHERE content_type = 'AI経理秘書';
            """)
            conn.commit()
            print("🧹 テストデータを削除しました")
        else:
            print("⚠️ テストデータの確認に失敗しました")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 cancellation_historyテーブルの作成が完了しました！")
        print("\n📝 次のステップ:")
        print("1. AIコレクションズメインアプリで解約時にこのテーブルに記録する機能を実装")
        print("2. AI経理秘書LINE Botでこのテーブルを参照して制限チェックを実装")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ データベースエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 cancellation_historyテーブル作成スクリプト")
    print("=" * 50)
    
    success = create_cancellation_history_table()
    
    if success:
        print("\n✅ スクリプトが正常に完了しました")
        sys.exit(0)
    else:
        print("\n❌ スクリプトが失敗しました")
        sys.exit(1)

if __name__ == "__main__":
    main() 