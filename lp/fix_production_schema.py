#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本番環境のデータベーススキーマ修正スクリプト
"""

import os
import sys
import logging
from utils.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_production_schema():
    """本番環境のデータベーススキーマを修正"""
    logger.info("🔄 本番環境データベーススキーマ修正開始")
    
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. 既存のcompany_contentsテーブルの構造を確認
        logger.info("📋 既存のテーブル構造を確認中...")
        c.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'company_contents'
            ORDER BY ordinal_position
        """)
        
        existing_columns = [row[0] for row in c.fetchall()]
        logger.info(f"既存のカラム: {existing_columns}")
        
        # 2. 新しいスキーマに合わせてテーブルを再作成
        logger.info("🔧 テーブルスキーマを修正中...")
        
        # 既存のテーブルを削除
        c.execute("DROP TABLE IF EXISTS company_contents CASCADE")
        
        # 新しいスキーマでテーブルを作成
        c.execute('''
            CREATE TABLE company_contents (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL,
                content_name VARCHAR(255) NOT NULL,
                content_type VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        ''')
        
        # 3. インデックスを作成
        c.execute('CREATE INDEX idx_company_contents_company_id ON company_contents(company_id)')
        c.execute('CREATE INDEX idx_company_contents_status ON company_contents(status)')
        
        conn.commit()
        logger.info("✅ データベーススキーマ修正完了")
        
        # 4. 修正後のテーブル構造を確認
        c.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'company_contents'
            ORDER BY ordinal_position
        """)
        
        new_columns = [row[0] for row in c.fetchall()]
        logger.info(f"修正後のカラム: {new_columns}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ データベーススキーマ修正エラー: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = fix_production_schema()
    if success:
        logger.info("🎉 本番環境データベーススキーマ修正が正常に完了しました")
        sys.exit(0)
    else:
        logger.error("💥 本番環境データベーススキーマ修正に失敗しました")
        sys.exit(1)
