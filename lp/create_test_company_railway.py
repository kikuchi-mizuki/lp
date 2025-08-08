#!/usr/bin/env python3
"""
Railway用テスト企業データ作成スクリプト
"""

import psycopg2
import sys
import time
import random
import string

def generate_company_code():
    """企業コードを生成"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_test_companies():
    """テスト用企業データを作成"""
    print("=== Railway用テスト企業データ作成 ===")
    
    # Railwayの外部接続URL（環境変数から取得）
    import os
    database_url = os.getenv('RAILWAY_DATABASE_URL') or os.getenv('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL/RAILWAY_DATABASE_URL is not set')
    
    # テスト企業データ
    test_companies = [
        {
            "name": "株式会社テックソリューション",
            "email": "info@techsolution.co.jp",
            "phone": "03-1234-5678",
            "address": "東京都渋谷区渋谷1-1-1",
            "industry": "IT・ソフトウェア",
            "employee_count": 150
        },
        {
            "name": "グローバル商事株式会社",
            "email": "contact@global-trading.co.jp",
            "phone": "06-2345-6789",
            "address": "大阪府大阪市中央区本町1-2-3",
            "industry": "貿易・商社",
            "employee_count": 80
        },
        {
            "name": "未来建設株式会社",
            "email": "info@mirai-construction.co.jp",
            "phone": "052-3456-7890",
            "address": "愛知県名古屋市中区栄1-3-4",
            "industry": "建設・不動産",
            "employee_count": 200
        },
        {
            "name": "サステナブルフーズ株式会社",
            "email": "info@sustainable-foods.co.jp",
            "phone": "045-4567-8901",
            "address": "神奈川県横浜市西区みなとみらい1-4-5",
            "industry": "食品・農業",
            "employee_count": 120
        },
        {
            "name": "デジタルマーケティング株式会社",
            "email": "hello@digital-marketing.co.jp",
            "phone": "092-5678-9012",
            "address": "福岡県福岡市博多区博多駅前1-5-6",
            "industry": "マーケティング・広告",
            "employee_count": 60
        }
    ]
    
    try:
        # PostgreSQLに接続
        print(f"🔗 Railway PostgreSQLに接続中...")
        conn = psycopg2.connect(database_url)
        c = conn.cursor()
        
        print(f"✅ 接続成功！")
        
        created_companies = []
        
        # テスト企業を作成
        for i, company_data in enumerate(test_companies, 1):
            print(f"\n📋 企業 {i} を作成中: {company_data['name']}")
            
            try:
                # 企業コードを生成
                company_code = generate_company_code()
                
                # 企業を挿入
                c.execute('''
                    INSERT INTO companies (
                        company_name, company_code, email, phone, address, 
                        industry, employee_count, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    company_data['name'], company_code, company_data['email'],
                    company_data['phone'], company_data['address'], 
                    company_data['industry'], company_data['employee_count'], 'active'
                ))
                
                company_id = c.fetchone()[0]
                
                # LINEアカウント情報を作成（モック）
                line_channel_id = f"U{company_code.lower()}"
                line_channel_access_token = f"access_token_{company_code.lower()}"
                line_channel_secret = f"secret_{company_code.lower()}"
                
                c.execute('''
                    INSERT INTO company_line_accounts (
                        company_id, line_channel_id, line_channel_access_token,
                        line_channel_secret, line_basic_id, status
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    company_id, line_channel_id, line_channel_access_token,
                    line_channel_secret, f"@{company_code.lower()}", 'active'
                ))
                
                # 決済情報を作成（モック）
                stripe_customer_id = f"cus_{company_code.lower()}"
                c.execute('''
                    INSERT INTO company_payments (
                        company_id, stripe_customer_id, subscription_status
                    ) VALUES (%s, %s, %s)
                ''', (company_id, stripe_customer_id, 'active'))
                
                # コンテンツ情報を作成
                contents = [
                    ("AI経理秘書", "accounting_secretary"),
                    ("AI予定秘書", "schedule_secretary"),
                    ("AIタスクコンシェルジュ", "task_concierge")
                ]
                
                for content_name, content_type in contents:
                    c.execute('''
                        INSERT INTO company_contents (
                            company_id, content_type, content_name, status
                        ) VALUES (%s, %s, %s, %s)
                    ''', (company_id, content_type, content_name, 'active'))
                
                # 通知設定を作成
                notifications = [
                    ("payment_completion", "支払い完了通知"),
                    ("payment_failure", "支払い失敗通知"),
                    ("subscription_renewal", "契約更新通知"),
                    ("cancellation", "解約通知")
                ]
                
                for notification_type, description in notifications:
                    c.execute('''
                        INSERT INTO company_notifications (
                            company_id, notification_type, is_enabled, recipients
                        ) VALUES (%s, %s, %s, %s)
                    ''', (company_id, notification_type, True, '[]'))
                
                created_companies.append({
                    'id': company_id,
                    'name': company_data['name'],
                    'code': company_code,
                    'email': company_data['email']
                })
                
                print(f"  ✅ 企業作成成功: ID={company_id}, コード={company_code}")
                
            except Exception as e:
                print(f"  ❌ 企業作成失敗: {e}")
                continue
        
        conn.commit()
        
        # 作成結果を表示
        print(f"\n🎉 テスト企業データ作成完了")
        print(f"📊 作成された企業数: {len(created_companies)}")
        
        if created_companies:
            print(f"\n📋 作成された企業一覧:")
            for company in created_companies:
                print(f"  - {company['name']} (ID: {company['id']}, コード: {company['code']})")
        
        # データベース内の企業数を確認
        c.execute("SELECT COUNT(*) FROM companies")
        total_companies = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM company_line_accounts")
        total_line_accounts = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM company_payments")
        total_payments = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM company_contents")
        total_contents = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM company_notifications")
        total_notifications = c.fetchone()[0]
        
        print(f"\n📊 データベース統計:")
        print(f"  - 企業数: {total_companies}")
        print(f"  - LINEアカウント数: {total_line_accounts}")
        print(f"  - 決済情報数: {total_payments}")
        print(f"  - コンテンツ数: {total_contents}")
        print(f"  - 通知設定数: {total_notifications}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン処理"""
    success = create_test_companies()
    
    if success:
        print(f"\n✅ テスト企業データの作成が完了しました！")
        print(f"🎯 次のステップ:")
        print(f"   1. Railwayダッシュボードで企業管理テーブルを確認")
        print(f"   2. Flaskサーバーを起動してダッシュボードを確認")
        print(f"   3. APIエンドポイントで企業データを確認")
        return True
    else:
        print(f"\n❌ テスト企業データの作成に失敗しました")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 