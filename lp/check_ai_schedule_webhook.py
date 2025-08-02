#!/usr/bin/env python3
"""
AI予定秘書複製用Webhook URL設定確認・修正スクリプト
"""

import os
from utils.db import get_db_connection

def check_ai_schedule_webhook_settings():
    """AI予定秘書複製用のWebhook URL設定を確認"""
    try:
        print("=== AI予定秘書複製用Webhook URL設定確認 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. 現在の企業情報を確認
        c.execute('''
            SELECT c.id, c.company_name, c.company_code, cla.webhook_url, cla.line_channel_id
            FROM companies c
            LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
            ORDER BY c.id DESC
        ''')
        
        companies = c.fetchall()
        
        if not companies:
            print("❌ 企業データが見つかりません")
            return False
        
        print(f"📊 企業データ数: {len(companies)}件")
        
        # 2. 各企業のWebhook URL設定を確認
        for company_id, company_name, company_code, webhook_url, line_channel_id in companies:
            print(f"\n🔍 企業ID {company_id}: {company_name}")
            print(f"  企業コード: {company_code}")
            print(f"  LINEチャネルID: {line_channel_id}")
            print(f"  現在のWebhook URL: {webhook_url}")
            
            # 3. AI予定秘書用の正しいWebhook URLを生成
            # AI予定秘書は個別のRailwayプロジェクトで動作するため、
            # 各企業専用のWebhook URLが必要
            
            # 方法1: 企業IDベースのWebhook URL
            company_webhook_url = f"https://lp-production-9e2c.up.railway.app/webhook/{company_id}"
            
            # 方法2: 企業コードベースのWebhook URL
            company_code_webhook_url = f"https://lp-production-9e2c.up.railway.app/webhook/{company_code}"
            
            # 方法3: LINEチャネルIDベースのWebhook URL
            line_channel_webhook_url = f"https://lp-production-9e2c.up.railway.app/webhook/line/{line_channel_id}"
            
            print(f"  推奨Webhook URL（企業ID）: {company_webhook_url}")
            print(f"  推奨Webhook URL（企業コード）: {company_code_webhook_url}")
            print(f"  推奨Webhook URL（LINEチャネル）: {line_channel_webhook_url}")
            
            # 4. 現在のURLが正しいかチェック
            if webhook_url:
                if 'lp-production-9e2c.up.railway.app' in webhook_url:
                    print(f"  ✅ ドメインは正しい")
                    
                    # パス部分をチェック
                    if f"/webhook/{company_id}" in webhook_url:
                        print(f"  ✅ 企業IDベースのパスは正しい")
                    elif f"/webhook/{company_code}" in webhook_url:
                        print(f"  ✅ 企業コードベースのパスは正しい")
                    elif f"/webhook/line/{line_channel_id}" in webhook_url:
                        print(f"  ✅ LINEチャネルベースのパスは正しい")
                    else:
                        print(f"  ⚠️ パスが推奨形式と異なります")
                else:
                    print(f"  ❌ ドメインが間違っています")
            else:
                print(f"  ❌ Webhook URLが設定されていません")
        
        # 5. AI予定秘書の環境変数設定を確認
        print(f"\n⚙️ AI予定秘書環境変数設定確認")
        
        # 必要な環境変数
        required_env_vars = [
            'LINE_CHANNEL_ACCESS_TOKEN',
            'LINE_CHANNEL_SECRET', 
            'LINE_CHANNEL_ID',
            'COMPANY_ID',
            'COMPANY_NAME',
            'BASE_URL'
        ]
        
        for var in required_env_vars:
            value = os.getenv(var)
            if value:
                print(f"  ✅ {var}: 設定済み")
            else:
                print(f"  ❌ {var}: 未設定")
        
        # 6. AI予定秘書用の推奨Webhook URL形式を提案
        print(f"\n📋 AI予定秘書複製用Webhook URL推奨形式")
        print(f"1. 企業IDベース: https://lp-production-9e2c.up.railway.app/webhook/{company_id}")
        print(f"2. 企業コードベース: https://lp-production-9e2c.up.railway.app/webhook/{company_code}")
        print(f"3. LINEチャネルベース: https://lp-production-9e2c.up.railway.app/webhook/line/{line_channel_id}")
        
        print(f"\n🔧 AI予定秘書複製時の設定手順:")
        print(f"1. Railwayプロジェクトで環境変数を設定")
        print(f"2. LINE Developers ConsoleでWebhook URLを設定")
        print(f"3. Webhook URLの検証を実行")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ AI予定秘書Webhook設定確認エラー: {e}")
        return False

def generate_ai_schedule_webhook_url(company_id, company_code, line_channel_id):
    """AI予定秘書用のWebhook URLを生成"""
    try:
        print(f"\n=== AI予定秘書用Webhook URL生成 ===")
        
        base_url = "https://lp-production-9e2c.up.railway.app"
        
        # 複数の形式でWebhook URLを生成
        webhook_urls = {
            "企業IDベース": f"{base_url}/webhook/{company_id}",
            "企業コードベース": f"{base_url}/webhook/{company_code}",
            "LINEチャネルベース": f"{base_url}/webhook/line/{line_channel_id}",
            "統合ベース": f"{base_url}/webhook/ai-schedule/{company_id}"
        }
        
        print(f"📋 生成されたWebhook URL:")
        for name, url in webhook_urls.items():
            print(f"  {name}: {url}")
        
        # 推奨URLを返す
        recommended_url = webhook_urls["企業IDベース"]
        print(f"\n🎯 推奨Webhook URL: {recommended_url}")
        
        return recommended_url
        
    except Exception as e:
        print(f"❌ Webhook URL生成エラー: {e}")
        return None

def update_ai_schedule_webhook_url(company_id):
    """AI予定秘書用のWebhook URLを更新"""
    try:
        print(f"\n=== AI予定秘書用Webhook URL更新 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業情報を取得
        c.execute('''
            SELECT c.company_name, c.company_code, cla.line_channel_id, cla.webhook_url
            FROM companies c
            LEFT JOIN company_line_accounts cla ON c.id = cla.company_id
            WHERE c.id = %s
        ''', (company_id,))
        
        company_info = c.fetchone()
        
        if not company_info:
            print(f"❌ 企業ID {company_id} が見つかりません")
            return False
        
        company_name, company_code, line_channel_id, current_webhook_url = company_info
        
        print(f"🔍 企業: {company_name}")
        print(f"  現在のWebhook URL: {current_webhook_url}")
        
        # 新しいWebhook URLを生成
        new_webhook_url = generate_ai_schedule_webhook_url(company_id, company_code, line_channel_id)
        
        if new_webhook_url:
            # Webhook URLを更新
            c.execute('''
                UPDATE company_line_accounts 
                SET webhook_url = %s, updated_at = CURRENT_TIMESTAMP
                WHERE company_id = %s
            ''', (new_webhook_url, company_id))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Webhook URLを更新しました: {new_webhook_url}")
            return True
        else:
            print(f"❌ Webhook URL生成に失敗しました")
            return False
            
    except Exception as e:
        print(f"❌ Webhook URL更新エラー: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """メイン関数"""
    print("AI予定秘書複製用Webhook URL設定確認を開始します...")
    
    # 1. 現在の設定を確認
    if check_ai_schedule_webhook_settings():
        print("\n✅ AI予定秘書Webhook設定確認が完了しました")
        
        # 2. 最新の企業のWebhook URLを更新
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT MAX(id) FROM companies')
        latest_company_id = c.fetchone()[0]
        conn.close()
        
        if latest_company_id:
            print(f"\n🔄 最新の企業（ID: {latest_company_id}）のWebhook URLを更新中...")
            if update_ai_schedule_webhook_url(latest_company_id):
                print("✅ Webhook URL更新が完了しました")
            else:
                print("❌ Webhook URL更新に失敗しました")
    else:
        print("\n❌ AI予定秘書Webhook設定確認に失敗しました")

if __name__ == "__main__":
    main() 