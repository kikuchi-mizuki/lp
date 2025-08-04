#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
企業ID 1の設定情報を更新するスクリプト
"""

import sys
import json
sys.path.append('lp')
from utils.db import get_db_connection

def update_company_settings():
    """企業ID 1の設定情報を更新"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 更新する情報
        company_id = 1
        company_name = "株式会社サンプル"
        line_channel_id = "2007858939"
        line_access_token = "7DrmRKzZYZRT7uHBgKB7i8OMfaCDtSOBFWMTfW6v6pdB4ZyhqT"
        line_channel_secret = "915352d9dd5bbd718a3127e4c89ff528"
        railway_project_id = "0ea6e85b-2d42-4b30-a13e-6a44247dc860"
        railway_project_url = f"https://railway.app/project/{railway_project_id}"
        webhook_url = "https://task-bot-production-3d6c.up.railway.app/callback"
        
        # 環境変数の設定情報
        environment_variables = {
            "PORT": "3000",
            "COMPANY_ID": str(company_id),
            "COMPANY_NAME": company_name,
            "LINE_CHANNEL_ID": line_channel_id,
            "LINE_CHANNEL_ACCESS_TOKEN": line_access_token,
            "LINE_CHANNEL_SECRET": line_channel_secret,
            "FLASK_SECRET_KEY": "your_flask_secret_key_here",
            "TIMEZONE": "Asia/Tokyo",
            "DEFAULT_EVENT_DURATION": "60"
        }
        
        # 設定サマリー
        settings_summary = f"""
企業ID: {company_id}
企業名: {company_name}
LINEチャネルID: {line_channel_id}
RailwayプロジェクトID: {railway_project_id}
Webhook URL: {webhook_url}

環境変数設定:
- PORT=3000
- COMPANY_ID={company_id}
- COMPANY_NAME={company_name}
- LINE_CHANNEL_ID={line_channel_id}
- LINE_CHANNEL_ACCESS_TOKEN={line_access_token[:10]}...
- LINE_CHANNEL_SECRET={line_channel_secret[:10]}...
- FLASK_SECRET_KEY=your_flask_secret_key_here
- TIMEZONE=Asia/Tokyo

手動設定が必要な環境変数:
- DATABASE_URL=(既存の設定を使用)
- RAILWAY_TOKEN=(既存の設定を使用)
        """.strip()
        
        # company_line_accountsテーブルを更新
        c.execute('''
            UPDATE company_line_accounts 
            SET line_channel_access_token = %s,
                line_channel_secret = %s,
                railway_project_id = %s,
                railway_project_url = %s,
                webhook_url = %s,
                environment_variables = %s,
                settings_summary = %s,
                deployment_status = 'pending',
                updated_at = CURRENT_TIMESTAMP
            WHERE company_id = %s AND line_channel_id = %s
        ''', (
            line_access_token,
            line_channel_secret,
            railway_project_id,
            railway_project_url,
            webhook_url,
            json.dumps(environment_variables),
            settings_summary,
            company_id,
            line_channel_id
        ))
        
        if c.rowcount > 0:
            print(f"✅ 企業ID {company_id} の設定を更新しました")
        else:
            print(f"⚠️ 企業ID {company_id} の更新対象が見つかりませんでした")
        
        conn.commit()
        conn.close()
        
        # 更新後の情報を表示
        print("\n📋 更新された設定情報:")
        print(f"企業ID: {company_id}")
        print(f"企業名: {company_name}")
        print(f"LINEチャネルID: {line_channel_id}")
        print(f"RailwayプロジェクトID: {railway_project_id}")
        print(f"RailwayプロジェクトURL: {railway_project_url}")
        print(f"Webhook URL: {webhook_url}")
        
        print("\n🔧 手動設定が必要な環境変数:")
        for key, value in environment_variables.items():
            print(f"  {key}={value}")
        
        print("\n📋 次の手順:")
        print("1. Railwayダッシュボードでプロジェクトを開く")
        print("2. 上記の環境変数を手動で設定")
        print("3. GitHub Actionsワークフローを手動実行")
        print("4. デプロイ完了を確認")
        print("5. LINE Webhook URLを設定")
        
        return True
        
    except Exception as e:
        print(f"❌ 設定更新エラー: {e}")
        return False

if __name__ == "__main__":
    update_company_settings() 