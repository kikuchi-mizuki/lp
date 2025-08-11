#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
解約処理でコンテンツ名が正しく表示されるかデバッグするスクリプト
"""

import os
import sys
import logging
from utils.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_cancellation_content():
    """解約処理でコンテンツ名が正しく表示されるかデバッグ"""
    logger.info("🔄 解約処理コンテンツ名デバッグ開始")
    
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業ID 14のコンテンツを確認
        c.execute('''
            SELECT id, content_name, content_type, status, created_at
            FROM company_contents
            WHERE company_id = 14
            ORDER BY created_at ASC
        ''')
        
        contents = c.fetchall()
        logger.info(f"企業ID 14のコンテンツ数: {len(contents)}")
        
        for i, content in enumerate(contents, 1):
            content_id, content_name, content_type, status, created_at = content
            logger.info(f"  {i}. ID: {content_id}, 名前: {content_name}, タイプ: {content_type}, ステータス: {status}")
            
            # 解約処理で使用される表示名を計算
            if content_type == 'ai_schedule':
                display_name = 'AI予定秘書'
            elif content_type == 'ai_accounting':
                display_name = 'AI経理秘書'
            elif content_type == 'ai_task':
                display_name = 'AIタスクコンシェルジュ'
            else:
                display_name = content_name or content_type
                
            logger.info(f"     表示名: {display_name}")
        
        # 解約処理のシミュレーション
        logger.info("\n🔍 解約処理シミュレーション（1番目を解約）:")
        
        active_contents = [c for c in contents if c[3] == 'active']
        logger.info(f"アクティブコンテンツ数: {len(active_contents)}")
        
        if len(active_contents) > 0:
            # 1番目を解約対象とする
            target_content = active_contents[0]
            content_id, content_name, content_type, status, created_at = target_content
            
            # 表示名を計算
            if content_type == 'ai_schedule':
                display_name = 'AI予定秘書'
            elif content_type == 'ai_accounting':
                display_name = 'AI経理秘書'
            elif content_type == 'ai_task':
                display_name = 'AIタスクコンシェルジュ'
            else:
                display_name = content_name or content_type
                
            logger.info(f"解約対象: {display_name} (ID: {content_id}, タイプ: {content_type})")
            
            # 解約後のメッセージをシミュレーション
            cancelled_text = f'• {display_name}'
            success_message = f'✅ 以下のコンテンツの解約が完了しました：\n\n{cancelled_text}\n\n次回請求から料金が反映されます。'
            logger.info(f"解約完了メッセージ:\n{success_message}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ デバッグエラー: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = debug_cancellation_content()
    if success:
        logger.info("🎉 デバッグが正常に完了しました")
        sys.exit(0)
    else:
        logger.error("💥 デバッグに失敗しました")
        sys.exit(1)
