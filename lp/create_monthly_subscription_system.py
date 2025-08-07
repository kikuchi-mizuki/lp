#!/usr/bin/env python3
"""
月額基本料金とコンテンツ追加料金を分離するシステム
"""

import os
import sys
from dotenv import load_dotenv

# 現在のディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.db import get_db_connection, get_db_type

def create_monthly_subscription_system():
    """月額基本料金とコンテンツ追加料金を分離するシステムを作成"""
    print("🚀 月額基本料金システムの作成を開始します")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # データベースタイプを取得
        db_type = get_db_type()
        placeholder = '%s' if db_type == 'postgresql' else '?'
        
        print("=== 現在の状況確認 ===")
        c.execute(f'SELECT id, company_id, content_type, subscription_status, base_price, additional_price, total_price FROM company_subscriptions WHERE company_id = 5')
        current_subscriptions = c.fetchall()
        
        for sub in current_subscriptions:
            print(f"ID: {sub[0]}, 企業ID: {sub[1]}, コンテンツ: {sub[2]}, ステータス: {sub[3]}, 基本料金: {sub[4]}, 追加料金: {sub[5]}, 総料金: {sub[6]}")
        
        print("\n=== 月額基本サブスクリプションテーブル作成 ===")
        
        # 月額基本サブスクリプションテーブルを作成
        c.execute('''
            CREATE TABLE IF NOT EXISTS company_monthly_subscriptions (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL,
                stripe_subscription_id VARCHAR(255),
                subscription_status VARCHAR(50) DEFAULT 'active',
                monthly_base_price INTEGER DEFAULT 3900,
                current_period_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                current_period_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                UNIQUE(company_id)
            )
        ''')
        
        print("✅ 月額基本サブスクリプションテーブル作成完了")
        
        # コンテンツ追加料金テーブルを作成
        c.execute('''
            CREATE TABLE IF NOT EXISTS company_content_additions (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL,
                content_type VARCHAR(100) NOT NULL,
                additional_price INTEGER DEFAULT 1500,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                UNIQUE(company_id, content_type)
            )
        ''')
        
        print("✅ コンテンツ追加料金テーブル作成完了")
        
        # 既存のデータを新しい構造に移行
        print("\n=== データ移行開始 ===")
        
        # 企業ID=5の月額基本サブスクリプションを作成
        c.execute(f'''
            INSERT INTO company_monthly_subscriptions 
            (company_id, stripe_subscription_id, subscription_status, monthly_base_price, current_period_end)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ON CONFLICT (company_id) DO UPDATE SET
            stripe_subscription_id = EXCLUDED.stripe_subscription_id,
            subscription_status = EXCLUDED.subscription_status,
            current_period_end = EXCLUDED.current_period_end
        ''', (5, 'sub_1RtQTlIxg6C5hAVdgbiUs3Lh', 'active', 3900, '2025-09-07 09:51:21'))
        
        print("✅ 月額基本サブスクリプション作成完了")
        
        # 既存のコンテンツを追加料金テーブルに移行
        content_mapping = {
            'AI予定秘書': 0,  # 基本料金に含まれる
            'AI経理秘書': 1500,  # 追加料金
            'AIタスクコンシェルジュ': 1500  # 追加料金
        }
        
        for content_type, additional_price in content_mapping.items():
            c.execute(f'''
                INSERT INTO company_content_additions 
                (company_id, content_type, additional_price, status)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                ON CONFLICT (company_id, content_type) DO UPDATE SET
                additional_price = EXCLUDED.additional_price,
                status = EXCLUDED.status
            ''', (5, content_type, additional_price, 'active'))
        
        print("✅ コンテンツ追加料金データ移行完了")
        
        conn.commit()
        
        print("\n=== 移行後の状況確認 ===")
        
        # 月額基本サブスクリプション確認
        c.execute(f'SELECT company_id, stripe_subscription_id, subscription_status, monthly_base_price FROM company_monthly_subscriptions WHERE company_id = 5')
        monthly_sub = c.fetchone()
        if monthly_sub:
            print(f"月額基本サブスクリプション: 企業ID={monthly_sub[0]}, Stripe ID={monthly_sub[1]}, ステータス={monthly_sub[2]}, 基本料金={monthly_sub[3]}円")
        
        # コンテンツ追加料金確認
        c.execute(f'SELECT company_id, content_type, additional_price, status FROM company_content_additions WHERE company_id = 5')
        content_additions = c.fetchall()
        for addition in content_additions:
            print(f"コンテンツ追加: 企業ID={addition[0]}, コンテンツ={addition[1]}, 追加料金={addition[2]}円, ステータス={addition[3]}")
        
        conn.close()
        print("\n✅ 月額基本料金システム作成完了")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_monthly_subscription_system()
