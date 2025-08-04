#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
company_line_accountsテーブルに企業毎の設定情報を保存する機能を追加
"""

import os
import json
import sys

# lpディレクトリをパスに追加
sys.path.append('lp')
from utils.db import get_db_connection

def enhance_company_line_accounts_table():
    """company_line_accountsテーブルに設定情報カラムを追加"""
    try:
        print("=== company_line_accountsテーブルの拡張 ===")
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # 新しいカラムを追加
        new_columns = [
            "railway_project_id VARCHAR(255)",
            "railway_project_url VARCHAR(500)",
            "webhook_url VARCHAR(500)",
            "environment_variables TEXT",
            "deployment_status VARCHAR(50) DEFAULT 'pending'",
            "last_deployment_at TIMESTAMP",
            "settings_summary TEXT"
        ]
        
        for column_def in new_columns:
            column_name = column_def.split()[0]
            try:
                c.execute(f"ALTER TABLE company_line_accounts ADD COLUMN {column_def}")
                conn.commit()  # 各カラム追加後にコミット
                print(f"✅ カラム追加: {column_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"⚠️ カラム既存: {column_name}")
                else:
                    print(f"❌ カラム追加エラー {column_name}: {e}")
                    conn.rollback()  # エラー時はロールバック
        
        conn.close()
        
        print("✅ company_line_accountsテーブルの拡張が完了しました")
        return True
        
    except Exception as e:
        print(f"❌ テーブル拡張エラー: {e}")
        return False

def save_company_settings(company_id, line_channel_id, line_access_token, line_channel_secret, 
                         railway_project_id=None, railway_project_url=None, webhook_url=None):
    """企業の設定情報をcompany_line_accountsテーブルに保存"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 環境変数の設定情報
        environment_variables = {
            "PORT": "3000",
            "COMPANY_ID": str(company_id),
            "COMPANY_NAME": "株式会社サンプル",  # 実際の企業名を取得
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
LINEチャネルID: {line_channel_id}
RailwayプロジェクトID: {railway_project_id or '未設定'}
Webhook URL: {webhook_url or '未設定'}

環境変数設定:
- PORT=3000
- COMPANY_ID={company_id}
- COMPANY_NAME=株式会社サンプル
- LINE_CHANNEL_ID={line_channel_id}
- LINE_CHANNEL_ACCESS_TOKEN={line_access_token[:10]}...
- LINE_CHANNEL_SECRET={line_channel_secret[:10]}...
- FLASK_SECRET_KEY=your_flask_secret_key_here
- TIMEZONE=Asia/Tokyo
        """.strip()
        
        # 既存のレコードを確認
        c.execute('''
            SELECT id FROM company_line_accounts 
            WHERE company_id = %s AND line_channel_id = %s
        ''', (company_id, line_channel_id))
        
        existing_record = c.fetchone()
        
        if existing_record:
            # 既存レコードを更新
            c.execute('''
                UPDATE company_line_accounts 
                SET line_channel_access_token = %s,
                    line_channel_secret = %s,
                    railway_project_id = %s,
                    railway_project_url = %s,
                    webhook_url = %s,
                    environment_variables = %s,
                    settings_summary = %s,
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
            print(f"✅ 企業設定を更新しました: 企業ID {company_id}")
        else:
            # 新規レコードを作成
            c.execute('''
                INSERT INTO company_line_accounts (
                    company_id, line_channel_id, line_channel_access_token, line_channel_secret,
                    railway_project_id, railway_project_url, webhook_url,
                    environment_variables, settings_summary, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
            ''', (
                company_id,
                line_channel_id,
                line_access_token,
                line_channel_secret,
                railway_project_id,
                railway_project_url,
                webhook_url,
                json.dumps(environment_variables),
                settings_summary
            ))
            print(f"✅ 企業設定を保存しました: 企業ID {company_id}")
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'company_id': company_id,
            'railway_project_id': railway_project_id,
            'webhook_url': webhook_url,
            'environment_variables': environment_variables
        }
        
    except Exception as e:
        print(f"❌ 企業設定保存エラー: {e}")
        return {'success': False, 'error': str(e)}

def get_company_settings(company_id):
    """企業の設定情報を取得"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM company_line_accounts 
            WHERE company_id = %s AND status = 'active'
            ORDER BY updated_at DESC
            LIMIT 1
        ''', (company_id,))
        
        record = c.fetchone()
        conn.close()
        
        if record:
            return {
                'success': True,
                'data': record
            }
        else:
            return {
                'success': False,
                'error': '企業設定が見つかりません'
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def list_all_company_settings():
    """全企業の設定情報を一覧表示"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT 
                cla.company_id,
                c.company_name,
                cla.line_channel_id,
                cla.railway_project_id,
                cla.webhook_url,
                cla.deployment_status,
                cla.updated_at
            FROM company_line_accounts cla
            JOIN companies c ON cla.company_id = c.id
            WHERE cla.status = 'active'
            ORDER BY cla.updated_at DESC
        ''')
        
        records = c.fetchall()
        conn.close()
        
        print("=== 全企業設定一覧 ===")
        for record in records:
            company_id, company_name, line_channel_id, railway_project_id, webhook_url, deployment_status, updated_at = record
            print(f"企業ID: {company_id}")
            print(f"企業名: {company_name}")
            print(f"LINEチャネルID: {line_channel_id}")
            print(f"RailwayプロジェクトID: {railway_project_id or '未設定'}")
            print(f"Webhook URL: {webhook_url or '未設定'}")
            print(f"デプロイ状況: {deployment_status}")
            print(f"更新日時: {updated_at}")
            print("-" * 50)
        
        return {
            'success': True,
            'count': len(records),
            'data': records
        }
        
    except Exception as e:
        print(f"❌ 企業設定一覧取得エラー: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """メイン関数"""
    print("🚀 company_line_accountsテーブルの拡張と設定保存機能")
    
    # 1. テーブルの拡張
    if enhance_company_line_accounts_table():
        print("✅ テーブル拡張完了")
        
        # 2. サンプルデータの保存（既存の企業ID 48を更新）
        sample_result = save_company_settings(
            company_id=48,
            line_channel_id="2007858939",
            line_access_token="7DrmRKzZYZRT7uHBgKB7i8OMfaCDtSOBFWMTfW6v6pdB4ZyhqT",
            line_channel_secret="915352d9dd5bbd718a3127e4c89ff528",
            railway_project_id="0ea6e85b-2d42-4b30-a13e-6a44247dc860",
            railway_project_url="https://railway.app/project/0ea6e85b-2d42-4b30-a13e-6a44247dc860",
            webhook_url="https://task-bot-production-3d6c.up.railway.app/callback"
        )
        
        if sample_result['success']:
            print("✅ サンプル設定保存完了")
        
        # 3. 全企業設定の一覧表示
        list_all_company_settings()
        
    else:
        print("❌ テーブル拡張に失敗しました")

if __name__ == "__main__":
    main() 