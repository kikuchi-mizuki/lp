import os
import logging
import stripe
import datetime as dt
from flask import request, jsonify, url_for, render_template, redirect
from utils.db import get_db_connection

logger = logging.getLogger(__name__)

# Stripe設定
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
MONTHLY_PRICE_ID = os.getenv('STRIPE_MONTHLY_PRICE_ID')

def create_company_profile(company_data):
    """企業プロファイルを作成"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 企業基本情報を挿入
        c.execute('''
            INSERT INTO companies (company_name, email, status)
            VALUES (%s, %s, %s)
            RETURNING id
        ''', (company_data['company_name'], company_data['email'], 'active'))
        
        company_id = c.fetchone()[0]
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 企業プロファイル作成完了: {company_id}")
        return company_id
        
    except Exception as e:
        logger.error(f"❌ 企業プロファイル作成エラー: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise e

def upsert_company_profile_with_subscription(company_name: str, email: str, stripe_subscription_id: str) -> int:
    """企業プロファイルをサブスクリプション情報と共に作成・更新"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 既存企業の確認
        c.execute('SELECT id FROM companies WHERE email = %s', (email,))
        existing_company = c.fetchone()
        
        if existing_company:
            company_id = existing_company[0]
            # 既存企業の更新
            c.execute('''
                UPDATE companies 
                SET company_name = %s, status = 'active'
                WHERE id = %s
            ''', (company_name, company_id))
        else:
            # 新規企業の作成
            c.execute('''
                INSERT INTO companies (company_name, email, status)
                VALUES (%s, %s, 'active')
                RETURNING id
            ''', (company_name, email))
            company_id = c.fetchone()[0]
        
        # 先に企業情報の変更を確定させる
        conn.commit()

        # サブスクリプション情報の保存（別コネクションで実行されるため、企業側を先にコミットする）
        save_company_subscription(company_id, stripe_subscription_id)
        
        # 念のためコミット（既にコミット済みの場合は影響なし）
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 企業プロファイル更新完了: {company_id}")
        return company_id
        
    except Exception as e:
        logger.error(f"❌ 企業プロファイル更新エラー: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise e

def create_company_line_account(company_id, company_data):
    """企業LINEアカウントを作成"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # LINEアカウント情報を挿入
        c.execute('''
            INSERT INTO company_line_accounts (
                company_id, line_channel_id, line_channel_secret,
                line_channel_access_token, line_user_id, line_display_name,
                line_picture_url, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
        ''', (
            company_id,
            company_data.get('line_channel_id'),
            company_data.get('line_channel_secret'),
            company_data.get('line_channel_access_token'),
            company_data.get('line_user_id'),
            company_data.get('line_display_name'),
            company_data.get('line_picture_url')
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 企業LINEアカウント作成完了: {company_id}")
        
    except Exception as e:
        logger.error(f"❌ 企業LINEアカウント作成エラー: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise e

def save_company_subscription(company_id, stripe_subscription_id, content_type=None):
    """企業サブスクリプション情報を保存（Stripe実ステータスを反映）"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Stripeのサブスクリプション詳細を取得してステータス/期間を反映
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        status = subscription.get('status') or 'active'
        current_period_start = subscription.get('current_period_start')
        current_period_end = subscription.get('current_period_end')

        # エポック -> datetime 変換（存在時のみ）
        start_dt = dt.datetime.utcfromtimestamp(int(current_period_start)) if current_period_start else None
        end_dt = dt.datetime.utcfromtimestamp(int(current_period_end)) if current_period_end else None

        # デフォルトの基本料金はスキーマ既定値を採用（明示する場合は3900）
        monthly_base_price = 3900

        # UPSERT（企業単位で1レコード）
        c.execute('''
            INSERT INTO company_monthly_subscriptions (
                company_id, stripe_subscription_id, subscription_status,
                monthly_base_price, current_period_start, current_period_end
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (company_id) DO UPDATE SET
                stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                subscription_status = EXCLUDED.subscription_status,
                monthly_base_price = EXCLUDED.monthly_base_price,
                current_period_start = EXCLUDED.current_period_start,
                current_period_end = EXCLUDED.current_period_end,
                updated_at = CURRENT_TIMESTAMP
        ''', (company_id, stripe_subscription_id, status, monthly_base_price, start_dt, end_dt))

        # コンテンツ情報も保存（指定があれば）
        if content_type:
            c.execute('''
                INSERT INTO company_contents (
                    company_id, content_type, content_status
                ) VALUES (%s, %s, 'active')
                ON CONFLICT (company_id, content_type) DO UPDATE SET
                    content_status = 'active',
                    updated_at = CURRENT_TIMESTAMP
            ''', (company_id, content_type))

        conn.commit()
        conn.close()

        logger.info(f"✅ 企業サブスクリプション保存完了: {company_id} status={status}")

    except Exception as e:
        logger.error(f"❌ 企業サブスクリプション保存エラー: {e}")
        if conn:
            conn.rollback()
            conn.close()
        raise e

def calculate_company_pricing(company_id, content_types):
    """企業の料金計算"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 基本料金
        base_price = 3900
        
        # コンテンツ別料金
        content_prices = {
            'AI予定秘書': 0,  # 基本料金に含まれる
            'AI経理秘書': 2000,
            'AIタスク管理': 1500
        }
        
        total_price = base_price
        for content_type in content_types:
            if content_type in content_prices:
                total_price += content_prices[content_type]
        
        conn.close()
        
        return {
            'base_price': base_price,
            'content_prices': content_prices,
            'total_price': total_price
        }
        
    except Exception as e:
        logger.error(f"❌ 料金計算エラー: {e}")
        raise e
