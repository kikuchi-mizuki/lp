#!/usr/bin/env python3
"""
企業ID 16にコンテンツを追加するスクリプト
"""

import os
import sys
import logging
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import get_db_connection

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_company_16_content():
    """企業ID 16にコンテンツを追加"""
    logger.info("🔄 企業ID 16にコンテンツ追加開始")
    
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        company_id = 16
        
        # 既存のコンテンツ数を確認
        c.execute("""
            SELECT COUNT(*) as content_count
            FROM company_contents
            WHERE company_id = %s AND status = 'active'
        """, (company_id,))
        existing_count = c.fetchone()[0]
        logger.info(f"既存のアクティブコンテンツ数: {existing_count}")
        
        # AI経理秘書を追加
        c.execute("""
            INSERT INTO company_contents 
            (company_id, content_type, content_name, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (company_id, 'accounting', 'AI経理秘書', 'active'))
        
        # AI予定秘書を追加
        c.execute("""
            INSERT INTO company_contents 
            (company_id, content_type, content_name, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (company_id, 'schedule', 'AI予定秘書', 'active'))
        
        conn.commit()
        
        # 追加後のコンテンツ数を確認
        c.execute("""
            SELECT COUNT(*) as content_count
            FROM company_contents
            WHERE company_id = %s AND status = 'active'
        """, (company_id,))
        new_count = c.fetchone()[0]
        logger.info(f"追加後のアクティブコンテンツ数: {new_count}")
        
        # コンテンツ詳細を表示
        c.execute("""
            SELECT content_type, content_name, created_at
            FROM company_contents
            WHERE company_id = %s AND status = 'active'
            ORDER BY created_at
        """, (company_id,))
        
        contents = c.fetchall()
        logger.info("追加されたコンテンツ:")
        for content in contents:
            logger.info(f"  - {content[1]} ({content[0]}) - {content[2]}")
        
        logger.info("✅ コンテンツ追加完了")
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_company_16_content()
