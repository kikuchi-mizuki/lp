#!/usr/bin/env python3
"""
company_content_additionsテーブルにbilling_end_dateカラムを追加するスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# 現在のディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.db import get_db_connection, get_db_type

def add_billing_end_date_column():
    """company_content_additionsテーブルにbilling_end_dateカラムを追加"""
    print("🚀 billing_end_dateカラム追加を開始します")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプを取得
        db_type = get_db_type()
        
        print("=== 現在のテーブル構造確認 ===")
        c.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'company_content_additions'
            ORDER BY ordinal_position
        """)
        
        columns = c.fetchall()
        print("現在のカラム一覧:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} ({'NULL可' if col[2] == 'YES' else 'NULL不可'})")
        
        # billing_end_dateカラムが存在するかチェック
        billing_end_exists = any(col[0] == 'billing_end_date' for col in columns)
        
        if billing_end_exists:
            print("\n✅ billing_end_dateカラムは既に存在します")
        else:
            print("\n=== billing_end_dateカラムを追加 ===")
            c.execute("""
                ALTER TABLE company_content_additions 
                ADD COLUMN billing_end_date TIMESTAMP
            """)
            print("✅ billing_end_dateカラムを追加しました")
        
        # 既存データのbilling_end_dateを更新
        print("\n=== 既存データの請求期間を更新 ===")
        
        # 月額サブスクリプションの請求期間を取得
        c.execute("""
            SELECT cca.id, cca.company_id, cms.current_period_end
            FROM company_content_additions cca
            JOIN company_monthly_subscriptions cms ON cca.company_id = cms.company_id
            WHERE cca.billing_end_date IS NULL AND cca.status = 'active'
        """)
        
        updates_needed = c.fetchall()
        print(f"更新が必要なレコード数: {len(updates_needed)}")
        
        for record in updates_needed:
            addition_id, company_id, period_end = record
            c.execute("""
                UPDATE company_content_additions 
                SET billing_end_date = %s
                WHERE id = %s
            """, (period_end, addition_id))
            print(f"✅ レコードID {addition_id} の請求期間を更新: {period_end}")
        
        conn.commit()
        
        print("\n=== 更新後のテーブル構造確認 ===")
        c.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'company_content_additions'
            ORDER BY ordinal_position
        """)
        
        columns = c.fetchall()
        print("更新後のカラム一覧:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} ({'NULL可' if col[2] == 'YES' else 'NULL不可'})")
        
        # サンプルデータ確認
        print("\n=== サンプルデータ確認 ===")
        c.execute("""
            SELECT id, company_id, content_type, additional_price, status, billing_end_date
            FROM company_content_additions 
            LIMIT 3
        """)
        
        samples = c.fetchall()
        for sample in samples:
            print(f"ID: {sample[0]}, 企業ID: {sample[1]}, コンテンツ: {sample[2]}, 追加料金: {sample[3]}円, ステータス: {sample[4]}, 請求期限: {sample[5]}")
        
        conn.close()
        print("\n✅ billing_end_dateカラム追加完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_billing_end_date_column()
