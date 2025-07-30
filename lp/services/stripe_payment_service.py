#!/usr/bin/env python3
"""
Stripe決済連携サービス
企業ごとの決済管理・Webhook処理・自動通知機能
"""

import os
import stripe
import json
import time
from datetime import datetime, timedelta
from utils.db import get_db_connection
from services.line_api_service import line_api_service

class StripePaymentService:
    """Stripe決済連携サービス"""
    
    def __init__(self):
        self.stripe_api_key = os.getenv('STRIPE_SECRET_KEY')
        self.stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        self.monthly_price_id = os.getenv('STRIPE_MONTHLY_PRICE_ID')
        self.usage_price_id = os.getenv('STRIPE_USAGE_PRICE_ID')
        
        if self.stripe_api_key:
            stripe.api_key = self.stripe_api_key
    
    def create_company_customer(self, company_id, company_name, email):
        """企業用のStripe顧客を作成"""
        try:
            # Stripe顧客を作成
            customer = stripe.Customer.create(
                name=company_name,
                email=email,
                metadata={
                    'company_id': str(company_id),
                    'company_name': company_name
                }
            )
            
            # データベースに保存
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                INSERT INTO company_payments (
                    company_id, stripe_customer_id, stripe_subscription_id,
                    payment_status, subscription_status, current_period_start,
                    current_period_end, trial_start, trial_end
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (company_id) DO UPDATE SET
                    stripe_customer_id = EXCLUDED.stripe_customer_id,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                company_id, customer.id, None, 'pending', 'inactive',
                None, None, None, None
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'customer_id': customer.id,
                'message': f'Stripe顧客が正常に作成されました: {company_name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Stripe顧客作成に失敗しました: {company_name}'
            }
    
    def create_subscription(self, company_id, price_id, trial_days=14):
        """企業用のサブスクリプションを作成"""
        try:
            # 企業の決済情報を取得
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT stripe_customer_id, company_name
                FROM company_payments cp
                JOIN companies c ON cp.company_id = c.id
                WHERE cp.company_id = %s
            ''', (company_id,))
            
            result = c.fetchone()
            if not result:
                return {
                    'success': False,
                    'error': '企業の決済情報が見つかりません'
                }
            
            customer_id, company_name = result
            
            # Stripeサブスクリプションを作成
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                trial_period_days=trial_days,
                metadata={
                    'company_id': str(company_id),
                    'company_name': company_name
                }
            )
            
            # データベースを更新
            c.execute('''
                UPDATE company_payments
                SET stripe_subscription_id = %s,
                    subscription_status = %s,
                    current_period_start = %s,
                    current_period_end = %s,
                    trial_start = %s,
                    trial_end = %s,
                    payment_status = 'active',
                    updated_at = CURRENT_TIMESTAMP
                WHERE company_id = %s
            ''', (
                subscription.id, subscription.status,
                datetime.fromtimestamp(subscription.current_period_start),
                datetime.fromtimestamp(subscription.current_period_end),
                datetime.fromtimestamp(subscription.trial_start) if subscription.trial_start else None,
                datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None,
                company_id
            ))
            
            conn.commit()
            conn.close()
            
            # LINE通知を送信
            trial_end_date = datetime.fromtimestamp(subscription.trial_end).strftime('%Y-%m-%d') if subscription.trial_end else 'N/A'
            line_api_service.send_notification_to_company(
                company_id,
                'subscription_created',
                f'サブスクリプションが作成されました。トライアル期間: {trial_end_date}まで'
            )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'status': subscription.status,
                'trial_end': trial_end_date,
                'message': f'サブスクリプションが正常に作成されました: {company_name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'サブスクリプション作成に失敗しました: {company_name}'
            }
    
    def cancel_subscription(self, company_id):
        """企業のサブスクリプションを解約"""
        try:
            # 企業の決済情報を取得
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT stripe_subscription_id, company_name
                FROM company_payments cp
                JOIN companies c ON cp.company_id = c.id
                WHERE cp.company_id = %s
            ''', (company_id,))
            
            result = c.fetchone()
            if not result:
                return {
                    'success': False,
                    'error': '企業の決済情報が見つかりません'
                }
            
            subscription_id, company_name = result
            
            if not subscription_id:
                return {
                    'success': False,
                    'error': 'サブスクリプションIDが見つかりません'
                }
            
            # Stripeサブスクリプションを解約
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            
            # データベースを更新
            c.execute('''
                UPDATE company_payments
                SET subscription_status = 'canceled',
                    updated_at = CURRENT_TIMESTAMP
                WHERE company_id = %s
            ''', (company_id,))
            
            # 解約履歴を記録
            c.execute('''
                INSERT INTO company_cancellations (
                    company_id, cancelled_at, subscription_status,
                    current_period_start, current_period_end,
                    stripe_subscription_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                company_id, datetime.now(), subscription.status,
                datetime.fromtimestamp(subscription.current_period_start),
                datetime.fromtimestamp(subscription.current_period_end),
                subscription_id
            ))
            
            conn.commit()
            conn.close()
            
            # LINE通知を送信
            line_api_service.send_notification_to_company(
                company_id,
                'cancellation',
                f'サブスクリプションが解約されました。サービスは{datetime.fromtimestamp(subscription.current_period_end).strftime("%Y-%m-%d")}まで利用可能です。'
            )
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'status': subscription.status,
                'message': f'サブスクリプションが正常に解約されました: {company_name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'サブスクリプション解約に失敗しました: {company_name}'
            }
    
    def process_webhook(self, payload, signature):
        """Stripe Webhookを処理"""
        try:
            # Webhook署名を検証
            event = stripe.Webhook.construct_event(
                payload, signature, self.stripe_webhook_secret
            )
            
            # イベントタイプに応じて処理
            if event['type'] == 'invoice.payment_succeeded':
                return self._handle_payment_succeeded(event)
            elif event['type'] == 'invoice.payment_failed':
                return self._handle_payment_failed(event)
            elif event['type'] == 'customer.subscription.updated':
                return self._handle_subscription_updated(event)
            elif event['type'] == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(event)
            else:
                return {
                    'success': True,
                    'message': f'未処理のイベント: {event["type"]}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Webhook処理に失敗しました'
            }
    
    def _handle_payment_succeeded(self, event):
        """支払い成功時の処理"""
        try:
            invoice = event['data']['object']
            customer_id = invoice['customer']
            
            # 企業IDを取得
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT company_id, company_name
                FROM company_payments cp
                JOIN companies c ON cp.company_id = c.id
                WHERE cp.stripe_customer_id = %s
            ''', (customer_id,))
            
            result = c.fetchone()
            if not result:
                return {'success': False, 'error': '企業が見つかりません'}
            
            company_id, company_name = result
            
            # 決済情報を更新
            c.execute('''
                UPDATE company_payments
                SET payment_status = 'succeeded',
                    updated_at = CURRENT_TIMESTAMP
                WHERE company_id = %s
            ''', (company_id,))
            
            conn.commit()
            conn.close()
            
            # LINE通知を送信
            amount = invoice['amount_paid'] / 100  # セントから円に変換
            line_api_service.send_notification_to_company(
                company_id,
                'payment_completion',
                f'支払いが完了しました。金額: ¥{amount:,}'
            )
            
            return {
                'success': True,
                'company_id': company_id,
                'amount': amount,
                'message': f'支払い成功: {company_name}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_payment_failed(self, event):
        """支払い失敗時の処理"""
        try:
            invoice = event['data']['object']
            customer_id = invoice['customer']
            
            # 企業IDを取得
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT company_id, company_name
                FROM company_payments cp
                JOIN companies c ON cp.company_id = c.id
                WHERE cp.stripe_customer_id = %s
            ''', (customer_id,))
            
            result = c.fetchone()
            if not result:
                return {'success': False, 'error': '企業が見つかりません'}
            
            company_id, company_name = result
            
            # 決済情報を更新
            c.execute('''
                UPDATE company_payments
                SET payment_status = 'failed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE company_id = %s
            ''', (company_id,))
            
            conn.commit()
            conn.close()
            
            # LINE通知を送信
            line_api_service.send_notification_to_company(
                company_id,
                'payment_failure',
                f'支払いに失敗しました。カード情報をご確認ください。'
            )
            
            return {
                'success': True,
                'company_id': company_id,
                'message': f'支払い失敗: {company_name}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_subscription_updated(self, event):
        """サブスクリプション更新時の処理"""
        try:
            subscription = event['data']['object']
            customer_id = subscription['customer']
            
            # 企業IDを取得
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT company_id, company_name
                FROM company_payments cp
                JOIN companies c ON cp.company_id = c.id
                WHERE cp.stripe_customer_id = %s
            ''', (customer_id,))
            
            result = c.fetchone()
            if not result:
                return {'success': False, 'error': '企業が見つかりません'}
            
            company_id, company_name = result
            
            # サブスクリプション情報を更新
            c.execute('''
                UPDATE company_payments
                SET subscription_status = %s,
                    current_period_start = %s,
                    current_period_end = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE company_id = %s
            ''', (
                subscription['status'],
                datetime.fromtimestamp(subscription['current_period_start']),
                datetime.fromtimestamp(subscription['current_period_end']),
                company_id
            ))
            
            conn.commit()
            conn.close()
            
            # LINE通知を送信
            if subscription['status'] == 'active':
                line_api_service.send_notification_to_company(
                    company_id,
                    'subscription_renewal',
                    f'サブスクリプションが更新されました。次回更新日: {datetime.fromtimestamp(subscription["current_period_end"]).strftime("%Y-%m-%d")}'
                )
            
            return {
                'success': True,
                'company_id': company_id,
                'status': subscription['status'],
                'message': f'サブスクリプション更新: {company_name}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_subscription_deleted(self, event):
        """サブスクリプション削除時の処理"""
        try:
            subscription = event['data']['object']
            customer_id = subscription['customer']
            
            # 企業IDを取得
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT company_id, company_name
                FROM company_payments cp
                JOIN companies c ON cp.company_id = c.id
                WHERE cp.stripe_customer_id = %s
            ''', (customer_id,))
            
            result = c.fetchone()
            if not result:
                return {'success': False, 'error': '企業が見つかりません'}
            
            company_id, company_name = result
            
            # サブスクリプション情報を更新
            c.execute('''
                UPDATE company_payments
                SET subscription_status = 'canceled',
                    updated_at = CURRENT_TIMESTAMP
                WHERE company_id = %s
            ''', (company_id,))
            
            conn.commit()
            conn.close()
            
            # LINE通知を送信
            line_api_service.send_notification_to_company(
                company_id,
                'cancellation',
                f'サブスクリプションが終了しました。サービスは利用できなくなります。'
            )
            
            return {
                'success': True,
                'company_id': company_id,
                'message': f'サブスクリプション終了: {company_name}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_payment_status(self, company_id):
        """企業の決済状況を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT 
                    stripe_customer_id, stripe_subscription_id,
                    payment_status, subscription_status,
                    current_period_start, current_period_end,
                    trial_start, trial_end, created_at, updated_at
                FROM company_payments
                WHERE company_id = %s
            ''', (company_id,))
            
            result = c.fetchone()
            conn.close()
            
            if not result:
                return {
                    'success': False,
                    'error': '決済情報が見つかりません'
                }
            
            return {
                'success': True,
                'payment_info': {
                    'customer_id': result[0],
                    'subscription_id': result[1],
                    'payment_status': result[2],
                    'subscription_status': result[3],
                    'current_period_start': result[4].isoformat() if result[4] else None,
                    'current_period_end': result[5].isoformat() if result[5] else None,
                    'trial_start': result[6].isoformat() if result[6] else None,
                    'trial_end': result[7].isoformat() if result[7] else None,
                    'created_at': result[8].isoformat() if result[8] else None,
                    'updated_at': result[9].isoformat() if result[9] else None
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_all_payments(self):
        """全企業の決済情報を取得"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute('''
                SELECT 
                    cp.company_id,
                    c.company_name,
                    cp.stripe_customer_id,
                    cp.stripe_subscription_id,
                    cp.payment_status,
                    cp.subscription_status,
                    cp.current_period_end,
                    cp.created_at
                FROM company_payments cp
                JOIN companies c ON cp.company_id = c.id
                ORDER BY cp.created_at DESC
            ''')
            
            payments = []
            for row in c.fetchall():
                payments.append({
                    'company_id': row[0],
                    'company_name': row[1],
                    'customer_id': row[2],
                    'subscription_id': row[3],
                    'payment_status': row[4],
                    'subscription_status': row[5],
                    'current_period_end': row[6].isoformat() if row[6] else None,
                    'created_at': row[7].isoformat() if row[7] else None
                })
            
            conn.close()
            
            return {
                'success': True,
                'payments': payments,
                'total_count': len(payments)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# シングルトンインスタンス
stripe_payment_service = StripePaymentService() 