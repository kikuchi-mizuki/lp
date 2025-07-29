#!/usr/bin/env python3
import os
import sys
from utils.db import get_db_connection

def test_content_addition_postgres():
    """PostgreSQL用のコンテンツ追加テスト"""
    try:
        print("=== PostgreSQL用コンテンツ追加テスト ===")
        
        # テスト用のコンテンツ情報
        content_info = {
            '1': {
                'name': 'AI予定秘書',
                'price': 1500,
                "description": '日程調整のストレスから解放される、スケジュール管理の相棒',
                'usage': 'Googleカレンダーと連携し、LINEで予定の追加・確認・空き時間の提案まで。調整のやりとりに追われる時間を、もっとクリエイティブに使えるように。',
                'url': 'https://lp-production-9e2c.up.railway.app/schedule',
                'line_url': 'https://line.me/R/ti/p/@ai_schedule_secretary'
            },
            '2': {
                'name': 'AI経理秘書',
                'price': 1500,
                "description": '打合せ後すぐ送れる、スマートな請求書作成アシスタント',
                'usage': 'LINEで項目を送るだけで、見積書や請求書を即作成。営業から事務処理までを一気通貫でスムーズに。',
                'url': 'https://lp-production-9e2c.up.railway.app/accounting',
                'line_url': 'https://line.me/R/ti/p/@ai_accounting_secretary'
            },
            '3': {
                'name': 'AIタスクコンシェルジュ',
                'price': 1500,
                "description": '今日やるべきことを、ベストなタイミングで',
                'usage': '登録したタスクを空き時間に自動で配置し、理想的な1日をAIが提案。「やりたいのにできない」を、「自然にこなせる」毎日に。',
                'url': 'https://lp-production-9e2c.up.railway.app/task',
                'line_url': 'https://line.me/R/ti/p/@ai_task_concierge'
            }
        }
        
        # PostgreSQL用のテストユーザーID
        test_user_id = 4
        test_line_user_id = "Upostgres123456789"
        
        print(f"テストユーザーID: {test_user_id}")
        print(f"テストLINEユーザーID: {test_line_user_id}")
        
        # 各コンテンツをテスト追加
        for content_number, content in content_info.items():
            print(f"\n📋 コンテンツ {content_number}: {content['name']} をテスト追加中...")
            
            try:
                from services.line_service import handle_content_confirmation
                result = handle_content_confirmation(test_user_id, content, test_line_user_id)
                
                if result['status'] == 'success':
                    print(f"✅ 成功: {content['name']}")
                    print(f"   料金: {'無料' if result['is_free'] else '¥1,500'}")
                    print(f"   現在のコンテンツ数: {result['current_count']}")
                else:
                    print(f"❌ 失敗: {result['message']}")
                    
            except Exception as e:
                print(f"❌ エラー: {e}")
                import traceback
                traceback.print_exc()
        
        # 結果確認
        print(f"\n📊 テスト後のデータベース状況:")
        conn = get_db_connection()
        c = conn.cursor()
        
        # usage_logs確認
        c.execute('SELECT COUNT(*) FROM usage_logs WHERE user_id = %s', (test_user_id,))
        usage_count = c.fetchone()[0]
        print(f"  usage_logs: {usage_count}件")
        
        if usage_count > 0:
            c.execute('SELECT id, content_type, is_free, pending_charge, created_at FROM usage_logs WHERE user_id = %s ORDER BY created_at DESC', (test_user_id,))
            recent_usage = c.fetchall()
            print(f"  最新の利用記録:")
            for usage in recent_usage:
                print(f"    ID: {usage[0]}, Content: {usage[1]}, Free: {usage[2]}, Pending: {usage[3]}, Created: {usage[4]}")
        
        # subscription_periods確認
        c.execute('SELECT COUNT(*) FROM subscription_periods WHERE user_id = %s', (test_user_id,))
        period_count = c.fetchone()[0]
        print(f"  subscription_periods: {period_count}件")
        
        if period_count > 0:
            c.execute('SELECT id, content_type, stripe_subscription_id, subscription_status, created_at FROM subscription_periods WHERE user_id = %s ORDER BY created_at DESC', (test_user_id,))
            recent_periods = c.fetchall()
            print(f"  最新の期間記録:")
            for period in recent_periods:
                print(f"    ID: {period[0]}, Content: {period[1]}, Stripe: {period[2]}, Status: {period[3]}, Created: {period[4]}")
        
        # cancellation_history確認
        c.execute('SELECT COUNT(*) FROM cancellation_history WHERE user_id = %s', (test_user_id,))
        cancel_count = c.fetchone()[0]
        print(f"  cancellation_history: {cancel_count}件")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_content_addition_postgres() 