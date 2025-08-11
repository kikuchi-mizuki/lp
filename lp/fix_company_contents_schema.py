#!/usr/bin/env python3
"""
company_contentsテーブルにcurrent_period_endカラムを追加するスクリプト
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

def add_current_period_end_to_company_contents():
    """company_contentsテーブルにcurrent_period_endカラムを追加"""
    logger.info("🔄 company_contentsテーブルにcurrent_period_endカラムを追加開始")
    
    conn = None
    c = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 現在のテーブル構造を確認
        c.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'company_contents' 
            ORDER BY ordinal_position
        """)
        columns = c.fetchall()
        logger.info(f"現在のcompany_contentsテーブルのカラム: {[col[0] for col in columns]}")
        
        # current_period_endカラムが存在するかチェック
        column_names = [col[0] for col in columns]
        if 'current_period_end' in column_names:
            logger.info("✅ current_period_endカラムは既に存在します")
            return
        
        # current_period_endカラムを追加
        c.execute("""
            ALTER TABLE company_contents 
            ADD COLUMN current_period_end TIMESTAMP
        """)
        
        conn.commit()
        logger.info("✅ current_period_endカラムを追加しました")
        
        # 追加後のテーブル構造を確認
        c.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'company_contents' 
            ORDER BY ordinal_position
        """)
        columns_after = c.fetchall()
        logger.info(f"更新後のcompany_contentsテーブルのカラム: {[col[0] for col in columns_after]}")
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()
        logger.info("✅ 処理完了")

if __name__ == "__main__":
    add_current_period_end_to_company_contents()
