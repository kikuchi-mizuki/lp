#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本番環境にテストデータを追加するスクリプト
"""

import os
import sys
import logging
from utils.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_production_test_data():
    """本番環境にテストデータを追加"""
    logger.info("🔄 本番環境テストデータ追加開始")
    
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業ID 14の存在確認
        c.execute("SELECT id, company_name FROM companies WHERE id = 14")
        company = c.fetchone()
        
        if not company:
            logger.error("❌ 企業ID 14が見つかりません")
            return False
            
        logger.info(f"企業情報: ID={company[0]}, 名前={company[1]}")
        
        # テストデータを追加
        test_contents = [
            (14, 'AI予定秘書', 'line', 'active'),
            (14, 'AI経理秘書', 'line', 'active'),
            (14, 'AIタスクコンシェルジュ', 'line', 'active')
        ]
        
        for content in test_contents:
            c.execute('''
                INSERT INTO company_contents (company_id, content_name, content_type, status, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            ''', content)
            logger.info(f"✅ テストデータ追加: {content[1]}")
        
        conn.commit()
        logger.info("✅ テストデータ追加完了")
        
        # 追加されたデータを確認
        c.execute('''
            SELECT id, content_name, content_type, status, created_at
            FROM company_contents
            WHERE company_id = 14
            ORDER BY created_at DESC
        ''')
        
        contents = c.fetchall()
        logger.info(f"企業ID 14のコンテンツ数: {len(contents)}")
        for content in contents:
            logger.info(f"  - ID: {content[0]}, 名前: {content[1]}, タイプ: {content[2]}, ステータス: {content[3]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ テストデータ追加エラー: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = add_production_test_data()
    if success:
        logger.info("🎉 本番環境テストデータ追加が正常に完了しました")
        sys.exit(0)
    else:
        logger.error("💥 本番環境テストデータ追加に失敗しました")
        sys.exit(1)
