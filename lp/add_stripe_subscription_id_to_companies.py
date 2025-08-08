#!/usr/bin/env python3
"""
companiesテーブルにstripe_subscription_idカラムを追加するスクリプト
"""

import os
import sys
import logging
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def get_db_connection():
    """データベース接続を取得"""
    try:
        # Railwayの外部接続URLを使用
        database_url = "postgresql://postgres:WZgnjZezoefHmxbwRjUbiPhajtwubmUs@gondola.proxy.rlwy.net:16797/railway"
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"データベース接続エラー: {e}")
        return None

def add_stripe_subscription_id_column():
    """companiesテーブルにstripe_subscription_idカラムを追加"""
    logger.info("🚀 companiesテーブルにstripe_subscription_idカラムを追加開始")
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("❌ データベース接続に失敗しました")
            return False
        
        cursor = conn.cursor()
        
        # 現在のカラム一覧を確認
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'companies' 
            ORDER BY ordinal_position
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"📋 既存のカラム: {existing_columns}")
        
        # stripe_subscription_idカラムが存在するかチェック
        if 'stripe_subscription_id' in existing_columns:
            logger.info("✅ stripe_subscription_idカラムは既に存在します")
            return True
        
        # stripe_subscription_idカラムを追加
        logger.info("➕ stripe_subscription_idカラムを追加中...")
        cursor.execute("""
            ALTER TABLE companies 
            ADD COLUMN stripe_subscription_id VARCHAR(255)
        """)
        
        conn.commit()
        logger.info("✅ stripe_subscription_idカラムを追加しました")
        
        # 修正後のテーブル構造を確認
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'companies' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        logger.info("📋 修正後のcompaniesテーブル構造:")
        for col in columns:
            logger.info(f"  - {col[0]}: {col[1]} (NULL可: {col[2]}, デフォルト: {col[3]})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ エラーが発生しました: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def main():
    """メイン処理"""
    logger.info("=== companiesテーブルにstripe_subscription_idカラム追加 ===")
    
    success = add_stripe_subscription_id_column()
    
    if success:
        logger.info("🎉 stripe_subscription_idカラムの追加が完了しました")
        logger.info("📋 次のステップ:")
        logger.info("1. 決済チェック機能のテスト")
        logger.info("2. 企業登録システムの動作確認")
        logger.info("3. LINE Webhookの動作確認")
    else:
        logger.error("❌ stripe_subscription_idカラムの追加に失敗しました")

if __name__ == "__main__":
    main()
